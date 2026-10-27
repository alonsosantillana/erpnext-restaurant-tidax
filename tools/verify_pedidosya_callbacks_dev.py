"""Development-only HTTPS/RQ verification. Never enables the global scheduler.
Queue routing and developer_mode are changed only in this test process and its forked
work horses. Application producers, Frappe serialization and execute_job remain real.
"""
import hashlib
import json
import logging
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

BENCH = Path("/home/erpnext/frappe-bench")
SITE = "v15.local"
RECEIVER = Path("/home/erpnext/projects/pedidosya-mock-receiver")
EVENTS = ("accepted", "rejected", "prepared", "picked_up")
OPS = ("Table Order", "Restaurant Fulfillment", "POS Invoice", "Sales Invoice",
       "Payment Entry", "Stock Ledger Entry", "GL Entry", "Item Price")
FQN = "restaurant_management.integrations.pedidosya.service.send_callback"
RECOVERY = "restaurant_management.integrations.pedidosya.service.recover_pending_orders"


def require(value, code):
    if not value:
        raise AssertionError(code)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def main():
    require(Path.cwd().resolve() == BENCH / "sites", "run_from_development_sites")
    require((BENCH / "sites" / SITE / "site_config.json").is_file(), "development_site_required")
    sys.path.insert(0, str(RECEIVER))
    import frappe
    import requests
    from rq import Queue, Worker
    from frappe.utils import background_jobs as bg
    from restaurant_management.integrations.pedidosya import service, client
    from pedidosya_mock.security import make_credentials
    from pedidosya_mock.store import Store

    original_init = frappe.init
    def safe_init(*args, **kwargs):
        requested = kwargs.get("site", args[0] if args else None)
        require(requested == SITE, "development_site_only")
        original_init(*args, **kwargs)
        frappe.conf.developer_mode = 0  # Runtime only: never include locals in error traces.

    safe_init(site=SITE, sites_path=str(BENCH / "sites"))
    frappe.connect()
    prefix = "TDX-TEST-DEV-" + time.strftime("%m%d%H%M%S", time.gmtime()) + "-" + secrets.token_hex(2).upper()
    setting = prefix + "-CFG"
    queue_name = bg.generate_qname("tdx_callback_" + secrets.token_hex(8))
    queue = Queue(queue_name, connection=bg.get_redis_conn(), default_timeout=90)
    require(queue.count == 0 and not Worker.all(queue=queue), "private_queue_empty")
    cases = {
        "WACC": "accepted", "WREJ": "rejected", "WPRE": "prepared", "WPICK": "picked_up",
        "TACC": "accepted", "TREJ": "rejected", "PACC": "accepted", "PREJ": "rejected",
        "BADLOGIN": "prepared", "BADTOKEN": "prepared", "EXPIRED": "prepared",
    }
    names = {key: prefix + "-" + key for key in cases}
    existing_settings = frappe.get_all("PedidosYa Integration Settings", fields=["name"], pluck="name")
    existing_orders = frappe.get_all("PedidosYa Order", fields=["name"], pluck="name")
    for name in existing_orders:
        doc = frappe.get_doc("PedidosYa Order", name)
        require(doc.status in ("Test", "Accepted", "Rejected"), "existing_order_not_safe")
        require(not any(doc.get(event + "_callback_url") for event in EVENTS), "existing_callback_present")
    def baseline():
        return {
            "settings": digest([frappe.get_doc("PedidosYa Integration Settings", name).as_dict() for name in existing_settings]),
            "orders": digest([frappe.get_doc("PedidosYa Order", name).as_dict() for name in existing_orders]),
            "operational_counts": {dt: frappe.db.count(dt) for dt in OPS},
            "site_config": hashlib.sha256((BENCH / "sites" / SITE / "site_config.json").read_bytes()).hexdigest(),
            "common_config": hashlib.sha256((BENCH / "sites/common_site_config.json").read_bytes()).hexdigest(),
            "enable_scheduler": frappe.db.get_single_value("System Settings", "enable_scheduler"),
        }
    before = baseline()
    require(bool(frappe.conf.pause_scheduler) and not before["enable_scheduler"],
            "global_scheduler_must_remain_paused")
    require(not frappe.get_doc("Scheduled Job Type", {"method": RECOVERY}).is_job_in_queue(),
            "recovery_job_already_running")
    output = Path(os.environ["TDX_DEV_EVIDENCE"])
    output.parent.mkdir(parents=True, exist_ok=True)
    require(not output.exists(), "evidence_must_be_new")
    result = {"site": SITE, "prefix": prefix, "private_queue": queue_name,
              "scheduler_invocation": "targeted ScheduledJobType.enqueue(force=True); global scheduler remains paused",
              "transport_adaptation": "in-memory get_queue routing of short/default to a unique private RQ queue",
              "checks": [], "cycles": [], "jobs": []}
    created = []
    process = None
    context = tempfile.TemporaryDirectory(prefix="tdx-dev-https-")
    root = Path(context.name)
    root.chmod(0o700)
    old_ca = os.environ.get("REQUESTS_CA_BUNDLE")
    try:
        cert, key = root / "server.crt", root / "server.key"
        subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                        "-keyout", str(key), "-out", str(cert), "-subj", "/CN=localhost",
                        "-addext", "subjectAltName=DNS:localhost", "-days", "1", "-sha256"],
                       check=True, capture_output=True)
        key.chmod(0o600)
        os.environ["REQUESTS_CA_BUNDLE"] = str(cert)
        scenario, credentials, state = root / "scenario.json", root / "credentials.json", root / "state.sqlite"
        username, password = "tdx_mock_dev_" + secrets.token_hex(4), secrets.token_urlsafe(32)
        credentials.write_text(json.dumps(make_credentials(username, password)))
        credentials.chmod(0o600)
        active_run = [""]
        def mode(value, suffix):
            run = prefix + "-" + suffix
            pending = root / ".pending"
            pending.write_text(json.dumps({"run_id": run, "mode": value}))
            os.replace(pending, scenario)
            active_run[0] = run
        mode("success", "WORKER")
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        sock.listen(64)
        base = "https://localhost:" + str(sock.getsockname()[1])
        env = os.environ.copy()
        env.update(MOCK_CONFIG=str(scenario), MOCK_CREDENTIALS=str(credentials),
                   MOCK_STATE=str(state), PYTHONDONTWRITEBYTECODE="1")
        process = subprocess.Popen([
            str(RECEIVER / ".venv/bin/python"), "-B", "-m", "uvicorn",
            "pedidosya_mock.app:create_app", "--factory", "--fd", str(sock.fileno()),
            "--ssl-keyfile", str(key), "--ssl-certfile", str(cert), "--no-access-log",
            "--log-level", "critical", "--no-server-header"],
            cwd=RECEIVER, env=env, pass_fds=[sock.fileno()],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sock.close()
        for _ in range(100):
            require(process.poll() is None, "receiver_stopped")
            try:
                if requests.get(base + "/healthz", timeout=2).status_code == 200:
                    break
            except requests.RequestException:
                time.sleep(.05)
        else:
            raise AssertionError("receiver_health_timeout")
        with requests.Session() as system_trust:
            system_trust.trust_env = False
            try:
                system_trust.get(base + "/healthz", timeout=2)
            except requests.exceptions.SSLError:
                result["checks"].append("HTTPS certificate requires the process-scoped test CA")
            else:
                raise AssertionError("untrusted_certificate_accepted")
        store = Store(state)
        profile = frappe.get_all("POS Profile", filters={"disabled": 0}, fields=["name", "company"], limit=1)
        require(profile, "enabled_pos_profile_required")
        customer = frappe.db.get_value("Customer", {"disabled": 0}, "name")
        item = frappe.db.get_value("Item", {"disabled": 0, "is_sales_item": 1}, "name")
        require(customer and item, "test_references_required")
        refs = {"company": profile[0].company, "pos_profile": profile[0].name}
        cfg = frappe.get_doc({
            "doctype": "PedidosYa Integration Settings", "remote_id": setting,
            "enabled": 0, "environment": "Staging", "integration_flow": "Direct", "auto_accept": 0,
            **refs, "integration_user": "Administrator", "default_customer": customer,
            "fallback_contact_phone": "000000000", "default_payment_timing": "Prepaid",
            "api_base_url": base, "api_username": username, "api_password": password,
            "jwt_secret": secrets.token_urlsafe(48), "callback_allowed_hosts": "localhost",
            "item_mappings": [{"remote_code": prefix + "-ITEM", "item_code": item}],
        })
        cfg.insert(set_name=setting)
        for case, event in cases.items():
            doc = frappe.get_doc({
                "doctype": "PedidosYa Order", "status": "Test", "test_order": 1,
                "settings": setting, **refs, "middleware_token": names[case] + "-TOKEN",
                "remote_id": setting, "external_code": names[case],
                "rejection_reason": "ITEM_UNAVAILABLE", "rejection_message": "Synthetic rejection",
                "received_at": frappe.utils.now_datetime(),
            })
            doc.insert(set_name=names[case])
            created.append(names[case])
            if os.environ.get("TDX_DEV_FAIL_AT") == "before_fixture_commit":
                raise AssertionError("injected_failure_before_fixture_commit")
        frappe.db.commit()
        result["checks"].append("disabled configuration and eleven test inboxes created without operational links")

        def routing(qtype="default", is_async=True):
            require(qtype in ("default", "short"), "unexpected_queue")
            require(is_async, "async_queue_required")
            return queue

        def get_doc(case):
            frappe.db.rollback()
            doc = frappe.get_doc("PedidosYa Order", names[case])
            require(doc.settings == setting and doc.test_order and not doc.table_order and not doc.fulfillment,
                    "fixture_scope")
            return doc

        def arm(keys, statuses=False):
            for case in keys:
                doc = get_doc(case)
                values = {event + "_callback_url": "" for event in EVENTS}
                event = cases[case]
                values[event + "_callback_url"] = base + "/mock/orders/" + doc.name + "/" + event.replace("_", "-")
                if statuses:
                    require(event in ("accepted", "rejected"), "scheduler_fixture_event")
                    values["status"] = "Accepted" if event == "accepted" else "Rejected"
                doc.db_set(values)
                frappe.db.commit()

        def disarm(keys):
            for case in keys:
                doc = get_doc(case)
                doc.db_set({event + "_callback_url": "" for event in EVENTS})
                frappe.db.commit()

        def confirmed(case):
            return bool(get_doc(case).get(cases[case] + "_notified"))

        def run_worker(label):
            require(queue.count > 0, "no_test_jobs")
            # No shared queues are listened to or drained.
            worker = Worker([queue], connection=queue.connection, name=prefix + "-" + label)
            worker.work(burst=True, logging_level="CRITICAL", max_jobs=50)
            require(queue.count == 0, "private_queue_not_drained")
            require(not queue.started_job_registry.get_job_ids(), "test_job_still_running")

        def enqueue_case(case, label):
            service._queue(FQN, name=names[case], callback_event=cases[case],
                           job_id=prefix + ":" + case + ":" + label)
            frappe.db.commit()

        def record_jobs():
            # Only own private queue; no raw errors, headers or method arguments exported.
            all_ids = set(queue.finished_job_registry.get_job_ids() + queue.failed_job_registry.get_job_ids())
            result["jobs"] = []
            for job_id in sorted(all_ids):
                job = bg.Job.fetch(job_id, connection=queue.connection)
                require(job.kwargs.get("site") == SITE, "foreign_job_site")
                result["jobs"].append({
                    "id": job_id, "status": str(job.get_status()),
                    "method": job.kwargs.get("method"),
                    "started_at": str(job.started_at), "ended_at": str(job.ended_at),
                    "argument_names": sorted(job.kwargs.get("kwargs", {})),
                    "reserved_event": job.kwargs.get("event"),
                    "http_error": bool(job.exc_info and "HTTPError" in job.exc_info),
                })

        def cycle(label):
            frappe.db.rollback()
            scheduled = frappe.get_doc("Scheduled Job Type", {"method": RECOVERY})
            require(not scheduled.stopped and scheduled.cron_format == "*/5 * * * *", "unexpected_scheduled_job")
            require(scheduled.enqueue(force=True), "scheduled_job_not_enqueued")
            run_worker(label)
            frappe.db.rollback()
            log = frappe.get_all("Scheduled Job Log", filters={"scheduled_job_type": scheduled.name},
                                 fields=["name", "status", "creation"], order_by="creation desc", limit=1)
            require(log and log[0].status == "Complete", "scheduled_parent_failed")
            result["cycles"].append({"label": label, "status": log[0].status, "creation": str(log[0].creation)})

        with patch.object(frappe, "init", safe_init), patch.object(bg, "get_queue", routing):
            arm(("WACC", "WREJ", "WPRE", "WPICK"))
            for case in ("WACC", "WREJ", "WPRE", "WPICK"):
                enqueue_case(case, "CONTRACT")
            run_worker("CONTRACT")
            require(all(confirmed(c) for c in ("WACC", "WREJ", "WPRE", "WPICK")), "worker_contract_not_confirmed")
            ev = store.evidence(active_run[0], limit=1000)
            require(sorted(r["event"] for r in ev if r["result"] == "204") == sorted(e.replace("_", "-") for e in EVENTS),
                    "four_callback_evidence")
            result["checks"].append("four native callback jobs completed through real RQ and verified HTTPS contracts")

            mode("fail-first", "TRANSIENT")
            arm(("TACC", "TREJ"), statuses=True)
            cycle("TRANSIENT1")
            require(not confirmed("TACC") and not confirmed("TREJ"), "failure_confirmed_notification")
            cycle("TRANSIENT2")
            require(confirmed("TACC") and confirmed("TREJ"), "recovery_did_not_confirm")
            ev = store.evidence(active_run[0], limit=1000)
            for case in ("TACC", "TREJ"):
                require([r["result"] for r in ev if r["test_id"].endswith(":" + names[case])] == ["503_transient", "204"],
                        "transient_retry_evidence")
            before_count = len(ev)
            cycle("NO-DUPLICATE")
            require(len(store.evidence(active_run[0], limit=1000)) == before_count, "scheduler_resent_confirmed_callback")
            result["checks"].append("targeted scheduled recovery retries accepted/rejected 503 then 204 and skips confirmed callbacks")

            mode("always-fail", "PERSISTENT")
            arm(("PACC", "PREJ"), statuses=True)
            cycle("PERSISTENT1")
            cycle("PERSISTENT2")
            require(not confirmed("PACC") and not confirmed("PREJ"), "persistent_error_confirmed")
            ev = store.evidence(active_run[0], limit=1000)
            for case in ("PACC", "PREJ"):
                require([r["result"] for r in ev if r["test_id"].endswith(":" + names[case])] ==
                        ["503_persistent", "503_persistent"], "persistent_retry_evidence")
            disarm(("PACC", "PREJ"))
            result["checks"].append("persistent HTTP503 retains both notification flags across two scheduled recoveries")

            mode("success", "AUTH")
            arm(("BADLOGIN", "BADTOKEN", "EXPIRED"))
            cache_key = "pedidosya:access-token:" + setting
            frappe.cache.delete_value(cache_key)
            cfg = frappe.get_doc("PedidosYa Integration Settings", setting)
            cfg.api_password = secrets.token_urlsafe(32)
            cfg.save()
            frappe.db.commit()
            enqueue_case("BADLOGIN", "INVALID")
            run_worker("BADLOGIN")
            require(not confirmed("BADLOGIN"), "bad_login_confirmed")
            require(store.evidence(active_run[0])[-1]["event"] == "login" and
                    store.evidence(active_run[0])[-1]["result"] == "401", "bad_login_evidence")
            cfg = frappe.get_doc("PedidosYa Integration Settings", setting)
            cfg.api_password = password
            cfg.save()
            frappe.db.commit()
            enqueue_case("BADLOGIN", "RESTORED")
            run_worker("LOGIN-RESTORED")
            require(confirmed("BADLOGIN"), "restored_login_failed")

            # Exercise the real Redis Lua comparison with synthetic credentials.
            # A newer worker's value must survive invalidation of an older token.
            rejected, renewed = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            frappe.cache.set_value(cache_key, renewed, expires_in_sec=300)
            frappe.local.cache[frappe.cache.make_key(cache_key)] = rejected
            client._invalidate_access_token(cfg, rejected)
            require(frappe.cache.make_key(cache_key) not in frappe.local.cache,
                    "stale_request_local_token_retained")
            require(frappe.cache.get_value(cache_key, expires=True) == renewed,
                    "concurrently_renewed_token_deleted")
            client._invalidate_access_token(cfg, renewed)
            require(frappe.cache.get_value(cache_key, expires=True) is None,
                    "matching_rejected_token_not_deleted")
            result["checks"].append("real Redis atomic invalidation preserves a newer token and removes only a matching token")

            invalid = secrets.token_urlsafe(32)
            frappe.cache.set_value(cache_key, invalid, expires_in_sec=300)
            auth_before = len(store.evidence(active_run[0], limit=1000))
            enqueue_case("BADTOKEN", "AUTO-REFRESH")
            run_worker("BADTOKEN")
            require(confirmed("BADTOKEN"), "invalid_token_automatic_recovery_failed")
            ev = store.evidence(active_run[0], limit=1000)[auth_before:]
            require([(r["event"], r["result"]) for r in ev] ==
                    [("prepared", "401"), ("login", "200"), ("prepared", "204")],
                    "invalid_token_bounded_renewal_sequence")
            token = frappe.cache.get_value(cache_key, expires=True)
            require(bool(token), "test_token_required")
            require(token != invalid, "invalid_token_not_replaced")
            with store.transaction() as db:
                updated = db.execute("UPDATE tokens SET expires=0 WHERE digest=?", (Store.token_hash(token),)).rowcount
                require(updated == 1, "token_expiry_scope")
            auth_before = len(store.evidence(active_run[0], limit=1000))
            enqueue_case("EXPIRED", "AUTO-REFRESH")
            run_worker("EXPIRED")
            require(confirmed("EXPIRED"), "expired_token_recovery_failed")
            ev = store.evidence(active_run[0], limit=1000)[auth_before:]
            require([(r["event"], r["result"]) for r in ev] ==
                    [("prepared", "401"), ("login", "200"), ("prepared", "204")],
                    "expired_token_bounded_renewal_sequence")
            require(frappe.cache.get_value(cache_key, expires=True) != token,
                    "expired_token_not_replaced")
            ev = store.evidence(active_run[0], limit=1000)
            require([r["result"] for r in ev if r["test_id"].endswith(":" + names["BADTOKEN"])] ==
                    ["401", "204"], "bad_token_sequence")
            require([r["result"] for r in ev if r["test_id"].endswith(":" + names["EXPIRED"])] ==
                    ["401", "204"], "expired_token_sequence")
            result["checks"].append("bad credentials do not confirm; invalid and expired tokens recover automatically within one RQ job each: callback401/login200/callback204")
            record_jobs()
        result["receiver_evidence"] = []
        for suffix in ("WORKER", "TRANSIENT", "PERSISTENT", "AUTH"):
            result["receiver_evidence"].extend(store.evidence(prefix + "-" + suffix, limit=1000))
        result["passed"] = True
    except Exception as exc:
        result["passed"] = False
        result["failure_type"] = type(exc).__name__
        # Only assertion codes are safe; never serialize HTTP exceptions/tracebacks.
        if isinstance(exc, AssertionError):
            result["failure_code"] = str(exc)
        raise
    finally:
        # Cleanup steps are independent: even a DB/scope error must stop our receiver,
        # restore the process environment and preserve sanitized evidence.
        cleanup_errors = []
        def attempt(label, operation, default=None):
            try:
                return operation()
            except Exception as cleanup_error:
                cleanup_errors.append({"step": label, "error_type": type(cleanup_error).__name__})
                return default

        attempt("rollback", frappe.db.rollback)
        def close_record(name):
            if not frappe.db.exists("PedidosYa Order", name):
                return  # An insert rolled back before the initial fixture commit.
            doc = frappe.get_doc("PedidosYa Order", name)
            require(doc.settings == setting and doc.test_order and not doc.table_order and not doc.fulfillment,
                    "cleanup_scope")
            doc.db_set({event + "_callback_url": "" for event in EVENTS})
            frappe.db.commit()
        for name in created:
            attempt("close_test_record", lambda name=name: close_record(name))
        def close_setting():
            if frappe.db.exists("PedidosYa Integration Settings", setting):
                doc = frappe.get_doc("PedidosYa Integration Settings", setting)
                require(doc.remote_id == setting, "cleanup_setting_scope")
                doc.db_set("enabled", 0)
                frappe.db.commit()
        attempt("disable_test_setting", close_setting)
        attempt("clear_test_cache", lambda: frappe.cache.delete_value("pedidosya:access-token:" + setting))
        # Raw GET must propagate Redis errors: get_value silently returns None
        # on connection failure and could incorrectly attest successful cleanup.
        test_cache_removed = attempt("verify_test_cache", lambda: frappe.cache.get(
            frappe.cache.make_key("pedidosya:access-token:" + setting)) is None, False)

        def cancel_pending():
            for job_id in queue.get_job_ids():
                job = bg.Job.fetch(job_id, connection=queue.connection)
                require(job.kwargs.get("site") == SITE, "cleanup_job_site")
                method = job.kwargs.get("method")
                args = job.kwargs.get("kwargs", {})
                require((method == FQN and args.get("name") in created)
                        or (method == "frappe.core.doctype.scheduled_job_type.scheduled_job_type.run_scheduled_job"
                            and args.get("job_type") == RECOVERY), "cleanup_job_scope")
                job.cancel()
        attempt("cancel_own_pending_jobs", cancel_pending)
        def urls_are_closed():
            return all(not any(frappe.get_doc("PedidosYa Order", name).get(event + "_callback_url")
                               for event in EVENTS)
                       for name in created if frappe.db.exists("PedidosYa Order", name))
        urls_removed = attempt("verify_urls", urls_are_closed, False)
        after = attempt("verify_baseline", baseline)
        result["cleanup"] = {
            "test_urls_removed": urls_removed,
            "test_cache_removed": test_cache_removed,
            "test_setting_disabled": attempt("verify_setting", lambda: not bool(
                frappe.db.get_value("PedidosYa Integration Settings", setting, "enabled")), False),
            "existing_config_and_records_unchanged": before == after,
            "operational_counts_before": before["operational_counts"],
            "operational_counts_after": after["operational_counts"] if after else None,
            "global_scheduler_enable_unchanged": bool(after and before["enable_scheduler"] == after["enable_scheduler"]),
            "private_queue_empty": attempt("verify_private_queue", lambda: queue.count == 0, False),
        }
        def stop_receiver():
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        attempt("stop_temporary_receiver", stop_receiver)
        result["cleanup"]["temporary_receiver_stopped"] = process is None or process.poll() is not None
        if old_ca is None:
            os.environ.pop("REQUESTS_CA_BUNDLE", None)
        else:
            os.environ["REQUESTS_CA_BUNDLE"] = old_ca
        result["cleanup"]["test_ca_environment_restored"] = os.environ.get("REQUESTS_CA_BUNDLE") == old_ca
        attempt("remove_temporary_resources", context.cleanup)
        result["cleanup"]["temporary_resources_removed"] = not root.exists()
        attempt("destroy_frappe_context", frappe.destroy)
        result["cleanup"]["errors"] = cleanup_errors
        if cleanup_errors or not all(result["cleanup"].get(key) for key in (
                "test_urls_removed", "test_cache_removed", "test_setting_disabled", "existing_config_and_records_unchanged",
                "global_scheduler_enable_unchanged", "private_queue_empty", "temporary_receiver_stopped",
                "test_ca_environment_restored", "temporary_resources_removed")):
            result["passed"] = False
            result.setdefault("failure_code", "cleanup_integrity")
        output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    require(result["passed"], "development_verification_failed")
    print(json.dumps({"passed": result["passed"], "checks": result["checks"],
                      "cycles": len(result["cycles"]), "jobs": len(result["jobs"]),
                      "cleanup": result["cleanup"], "evidence": str(output)}))


if __name__ == "__main__":
    main()
