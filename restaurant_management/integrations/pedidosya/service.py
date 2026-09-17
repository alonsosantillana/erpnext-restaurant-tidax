import hashlib
import json
from datetime import datetime, timedelta, timezone

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime

from restaurant_management.integrations.pedidosya.client import post_callback, validate_callback_url
from restaurant_management.integrations.pedidosya.parsing import (
    PayloadError,
    address_snapshot,
    contact_phone,
    delivery_fee,
    delivery_mode,
    external_total,
    normalize_lines,
    promised_at,
)


TERMINAL_STATUSES = {"Accepted", "Imported", "Test", "Rejected", "Cancelled"}
REJECTION_REASONS = {
    "ADDRESS_INCOMPLETE_MISSTATED", "BAD_WEATHER", "BLACKLISTED", "CARD_READER_NOT_AVAILABLE",
    "CLOSED", "FRAUD_PRANK", "ITEM_UNAVAILABLE", "MENU_ACCOUNT_SETTINGS", "NO_COURIER",
    "NO_PICKER", "NO_RESPONSE", "OUTSIDE_DELIVERY_AREA", "TECHNICAL_PROBLEM", "TEST_ORDER",
    "TOO_BUSY", "UNABLE_TO_PAY",
}


def _canonical_payload(payload):
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _callback(payload, *names):
    callbacks = payload.get("callbackUrls") or {}
    for name in names:
        value = callbacks.get(name) or payload.get(name)
        if value:
            return str(value)
    return None


def _queue(method, **kwargs):
    frappe.enqueue(
        method,
        queue="short",
        enqueue_after_commit=True,
        deduplicate=True,
        **kwargs,
    )


def receive_order(settings, payload):
    token = str(payload.get("token") or "").strip()
    code = str(payload.get("code") or "").strip()
    if not token or not code:
        raise PayloadError("PedidosYa payload requires token and code")
    serialized = _canonical_payload(payload)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    existing = frappe.db.get_value(
        "PedidosYa Order", {"middleware_token": token}, ["name", "payload_digest", "status"], as_dict=True
    )
    if existing:
        if existing.payload_digest != digest:
            raise PayloadError("The PedidosYa token was already used with different content")
        return {"remoteOrderId": existing.name, "status": existing.status}, False

    fulfillment_type, delivery_provider = delivery_mode(payload)
    total = external_total(payload)
    callback_values = {
        "accepted_callback_url": _callback(payload, "orderAccepted", "orderAcceptedUrl", "accepted"),
        "rejected_callback_url": _callback(payload, "orderRejected", "orderRejectedUrl", "rejected"),
        "prepared_callback_url": _callback(
            payload, "orderPreparedUpUrl", "orderPreparedUrl", "orderPrepared", "prepared"
        ),
        "picked_up_callback_url": _callback(payload, "orderPickedUp", "orderPickedUpUrl", "pickedUp"),
    }
    for url in callback_values.values():
        if url:
            try:
                validate_callback_url(settings, url)
            except frappe.ValidationError as exc:
                raise PayloadError(str(exc)) from exc
    doc = frappe.get_doc({
        "doctype": "PedidosYa Order",
        "settings": settings.name,
        "company": settings.company,
        "pos_profile": settings.pos_profile,
        "remote_id": settings.remote_id,
        "middleware_token": token,
        "external_code": code,
        "short_code": payload.get("shortCode"),
        "test_order": cint(payload.get("test")),
        "expedition_type": fulfillment_type,
        "delivery_provider": delivery_provider,
        "external_total": total,
        "currency": (payload.get("price") or {}).get("currency"),
        "payload": serialized,
        "payload_digest": digest,
        "received_at": now_datetime(),
        **callback_values,
    })
    try:
        doc.insert(ignore_permissions=True)
    except frappe.DuplicateEntryError:
        existing = frappe.db.get_value(
            "PedidosYa Order", {"middleware_token": token}, ["name", "payload_digest", "status"], as_dict=True
        )
        if not existing or existing.payload_digest != digest:
            raise PayloadError("The PedidosYa token was already used with different content")
        return {"remoteOrderId": existing.name, "status": existing.status}, False
    _queue(
        "restaurant_management.integrations.pedidosya.service.process_order",
        job_id=f"pedidosya-import:{doc.name}",
        name=doc.name,
    )
    return {"remoteOrderId": doc.name, "status": doc.status}, True


def _mapping_by_remote_code(settings):
    return {row.remote_code: row for row in settings.item_mappings}


def _item_entry(line):
    item = frappe.get_cached_doc("Item", line["item_code"])
    if item.disabled or not item.is_sales_item:
        raise PayloadError(f"Mapped item {item.name} is not available for sale")
    return {
        "identifier": f"pya_{frappe.generate_hash(length=16)}",
        "item_code": item.name,
        "qty": float(line["qty"]),
        "rate": float(line["rate"]),
        "price_list_rate": float(line["rate"]),
        "discount_percentage": 0,
        "discount_amount": 0,
        "item_tax_template": None,
        "item_tax_rate": "{}",
        "status": "Attending",
        "notes": line["notes"],
        "ordered_finish": 0,
        "has_batch_no": cint(item.has_batch_no),
        "batch_no": None,
        "has_serial_no": cint(item.has_serial_no),
        "serial_no": None,
        "unit_value": 0,
    }


def _create_restaurant_documents(integration_order, settings, payload, lines):
    profile = frappe.get_cached_doc("POS Profile", settings.pos_profile)
    order = frappe.get_doc({
        "doctype": "Table Order",
        "service_type": integration_order.expedition_type,
        "status": "Attending",
        "company": settings.company,
        "pos_profile": settings.pos_profile,
        "customer": settings.default_customer,
        "guest_count": 0,
        "taxes_and_charges": profile.taxes_and_charges,
        "selling_price_list": profile.selling_price_list,
    })
    order.insert()
    for line in lines:
        order.update_item(_item_entry(line), unrestricted=True)
        order.aggregate()
        order.reload()
    fee = delivery_fee(payload)
    if fee:
        from restaurant_management.restaurant_management.company_settings import get_restaurant_settings

        restaurant_settings = get_restaurant_settings(
            company=settings.company,
            pos_profile=settings.pos_profile,
        )
        if not restaurant_settings.delivery_fee_item:
            frappe.throw(_("Configure a delivery fee Item before importing PedidosYa delivery charges"))
        order.add_delivery_fee_item(restaurant_settings.delivery_fee_item, float(fee))
        order.reload()

    expected = integration_order.external_total
    if expected not in (None, "") and abs(flt(order.amount) - flt(expected)) > flt(settings.amount_tolerance or 0.01):
        frappe.throw(
            _("PedidosYa total {0} differs from restaurant total {1}").format(expected, order.amount)
        )

    phone = contact_phone(payload) or settings.fallback_contact_phone
    snapshot = address_snapshot(payload)
    fulfillment = frappe.get_doc({
        "doctype": "Restaurant Fulfillment",
        "order": order.name,
        "fulfillment_type": integration_order.expedition_type,
        "customer": settings.default_customer,
        "contact_phone": phone,
        "address_display_snapshot": snapshot,
        "delivery_reference": ((payload.get("delivery") or {}).get("address") or {}).get("deliveryInstructions"),
        "instructions": payload.get("comments"),
        "order_channel": "PedidosYa",
        "delivery_provider": integration_order.delivery_provider,
        "external_order_id": integration_order.external_code,
        "promised_at": promised_at(payload),
        "delivery_fee": float(fee),
        "payment_timing": settings.default_payment_timing,
        "expected_payment_method": settings.expected_payment_method,
        "payment_status": "Paid" if settings.default_payment_timing == "Prepaid" else "Unpaid",
        "request_id": f"pedidosya:{integration_order.middleware_token}",
    })
    fulfillment.insert()
    return order, fulfillment


def process_order(name):
    previous_user = frappe.session.user
    savepoint = "pedidosya_import"
    try:
        integration_order = frappe.get_doc("PedidosYa Order", name)
        if integration_order.status in TERMINAL_STATUSES or integration_order.table_order:
            return
        settings = frappe.get_doc("PedidosYa Integration Settings", integration_order.settings)
        frappe.set_user(settings.integration_user)
        frappe.db.sql("SELECT name FROM `tabPedidosYa Order` WHERE name = %s FOR UPDATE", (name,))
        integration_order.reload()
        integration_order.db_set({"status": "Processing", "attempts": cint(integration_order.attempts) + 1, "last_error": None})
        payload = json.loads(integration_order.get_password("payload"))
        lines = normalize_lines(payload, _mapping_by_remote_code(settings))
        if integration_order.test_order:
            integration_order.db_set({"status": "Test", "processed_at": now_datetime()})
            return

        frappe.db.savepoint(savepoint)
        try:
            order, fulfillment = _create_restaurant_documents(integration_order, settings, payload, lines)
            integration_order.db_set({
                "table_order": order.name,
                "fulfillment": fulfillment.name,
                "processed_at": now_datetime(),
                "status": "Awaiting Acceptance" if settings.integration_flow == "Direct" and not settings.auto_accept else "Imported",
            })
        except Exception:
            frappe.db.rollback(save_point=savepoint)
            raise

        if settings.integration_flow == "Indirect" or settings.auto_accept:
            _accept(integration_order.name, automatic=True)
    except Exception as exc:
        if frappe.db.exists("PedidosYa Order", name):
            frappe.db.set_value("PedidosYa Order", name, {"status": "Error", "last_error": str(exc)[:500]})
        frappe.log_error(title=f"PedidosYa import failed: {name}", message=frappe.get_traceback())
    finally:
        frappe.set_user(previous_user)


def _accept(name, automatic=False):
    doc = frappe.get_doc("PedidosYa Order", name)
    if not automatic:
        doc.check_permission("write")
    if doc.status in {"Accepted", "Cancelled"}:
        return doc.status
    if doc.status not in {"Awaiting Acceptance", "Imported"} or not doc.table_order:
        frappe.throw(_("This PedidosYa order cannot be accepted"))
    order = frappe.get_doc("Table Order", doc.table_order)
    order.send
    doc.db_set({"status": "Accepted", "processed_at": now_datetime()})
    settings = frappe.get_doc("PedidosYa Integration Settings", doc.settings)
    if settings.integration_flow == "Direct" and doc.accepted_callback_url and not doc.accepted_notified:
        _queue(
            "restaurant_management.integrations.pedidosya.service.send_callback",
            job_id=f"pedidosya-accepted:{doc.name}",
            name=doc.name,
            event="accepted",
        )
    return "Accepted"


@frappe.whitelist(methods=["POST"])
def accept_order(name):
    return _accept(name)


@frappe.whitelist(methods=["POST"])
def reject_order(name, reason, message=None):
    doc = frappe.get_doc("PedidosYa Order", name)
    doc.check_permission("write")
    if doc.status != "Awaiting Acceptance":
        frappe.throw(_("Only an order awaiting acceptance can be rejected"))
    reason = str(reason or "").strip().upper()
    if not reason:
        frappe.throw(_("Enter a rejection reason"))
    if reason not in REJECTION_REASONS:
        frappe.throw(_("Select a valid PedidosYa rejection reason"))
    message = str(message or "").strip()[:300]
    if doc.fulfillment:
        frappe.get_doc("Restaurant Fulfillment", doc.fulfillment)._transition("Cancelled", reason=reason, automatic=True)
    doc.db_set({
        "status": "Rejected",
        "last_error": message or reason,
        "rejection_reason": reason,
        "rejection_message": message,
    })
    if doc.rejected_callback_url:
        _queue(
            "restaurant_management.integrations.pedidosya.service.send_callback",
            job_id=f"pedidosya-rejected:{doc.name}",
            name=doc.name,
            event="rejected",
            reason=reason,
            message=message,
        )
    return "Rejected"


@frappe.whitelist(methods=["POST"])
def retry_order(name):
    doc = frappe.get_doc("PedidosYa Order", name)
    doc.check_permission("write")
    if doc.status not in {"Error", "Review"} or doc.table_order:
        frappe.throw(_("This PedidosYa order cannot be retried automatically"))
    doc.db_set("status", "Received")
    _queue(
        "restaurant_management.integrations.pedidosya.service.process_order",
        job_id=f"pedidosya-retry:{doc.name}:{cint(doc.attempts) + 1}",
        name=doc.name,
    )


def send_callback(name, event, reason=None, message=None):
    doc = frappe.get_doc("PedidosYa Order", name)
    settings = frappe.get_doc("PedidosYa Integration Settings", doc.settings)
    urls = {
        "accepted": doc.accepted_callback_url,
        "rejected": doc.rejected_callback_url,
        "prepared": doc.prepared_callback_url,
        "picked_up": doc.picked_up_callback_url,
    }
    url = urls.get(event)
    if not url:
        return
    payload = callback_payload(doc, settings, event, reason=reason, message=message)
    post_callback(settings, url, payload)
    values = {"last_event_at": now_datetime()}
    if event == "accepted":
        values["accepted_notified"] = 1
    elif event == "rejected":
        values["rejected_notified"] = 1
    elif event == "prepared":
        values["prepared_notified"] = 1
    elif event == "picked_up":
        values["picked_up_notified"] = 1
    doc.db_set(values)


def callback_payload(doc, settings, event, reason=None, message=None):
    if event == "accepted":
        minutes = max(cint(settings.default_preparation_minutes or 20), 2)
        return {
            "status": "order_accepted",
            "remoteOrderId": doc.name,
            "acceptanceTime": (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat(),
        }
    if event == "rejected":
        payload = {"status": "order_rejected", "reason": reason or doc.rejection_reason}
        rejection_message = message or doc.rejection_message
        if rejection_message:
            payload["message"] = rejection_message
        return payload
    if event == "picked_up":
        return {"status": "order_picked_up"}
    if event == "prepared":
        return None
    raise ValueError(f"Unsupported PedidosYa callback event: {event}")


def notify_prepared_by_fulfillment(fulfillment_name):
    name = frappe.db.get_value("PedidosYa Order", {"fulfillment": fulfillment_name}, "name")
    if not name:
        return
    fulfillment = frappe.db.get_value(
        "Restaurant Fulfillment", fulfillment_name, ["fulfillment_type", "delivery_provider"], as_dict=True
    )
    if not fulfillment or fulfillment.fulfillment_type != "Delivery" or fulfillment.delivery_provider != "PedidosYa":
        return
    doc = frappe.get_doc("PedidosYa Order", name)
    if doc.prepared_callback_url and not doc.prepared_notified:
        _queue(
            "restaurant_management.integrations.pedidosya.service.send_callback",
            job_id=f"pedidosya-prepared:{doc.name}",
            name=doc.name,
            event="prepared",
        )


def notify_picked_up_by_fulfillment(fulfillment_name):
    name = frappe.db.get_value("PedidosYa Order", {"fulfillment": fulfillment_name}, "name")
    if not name:
        return
    fulfillment = frappe.db.get_value(
        "Restaurant Fulfillment", fulfillment_name, ["fulfillment_type", "delivery_provider"], as_dict=True
    )
    if not fulfillment or (
        fulfillment.fulfillment_type == "Delivery" and fulfillment.delivery_provider == "PedidosYa"
    ):
        return
    doc = frappe.get_doc("PedidosYa Order", name)
    if doc.picked_up_callback_url and not doc.picked_up_notified:
        _queue(
            "restaurant_management.integrations.pedidosya.service.send_callback",
            job_id=f"pedidosya-picked-up:{doc.name}",
            name=doc.name,
            event="picked_up",
        )


def receive_status(settings, remote_order_id, payload):
    name = frappe.db.get_value(
        "PedidosYa Order", {"name": remote_order_id, "settings": settings.name}, "name"
    )
    if not name:
        frappe.throw(_("PedidosYa order was not found"), frappe.DoesNotExistError)
    status = str(payload.get("status") or payload.get("orderStatus") or "").upper().strip()
    if not status:
        raise PayloadError("PedidosYa status is required")
    frappe.db.set_value("PedidosYa Order", name, {"provider_status": status, "last_event_at": now_datetime()})
    _queue(
        "restaurant_management.integrations.pedidosya.service.process_status",
        job_id=f"pedidosya-status:{name}:{status}",
        name=name,
        status=status,
        reason=str(payload.get("reason") or "PedidosYa status update")[:300],
    )
    return {"remoteOrderId": name, "status": status}


def process_status(name, status, reason=None):
    doc = frappe.get_doc("PedidosYa Order", name)
    if not doc.fulfillment:
        return
    fulfillment = frappe.get_doc("Restaurant Fulfillment", doc.fulfillment)
    if status == "ORDER_CANCELLED":
        if fulfillment.status == "Cancelled":
            return
        if fulfillment.status in {"New", "Preparing", "Ready", "Assigned"}:
            fulfillment._transition("Cancelled", reason=reason, automatic=True)
            doc.db_set("status", "Cancelled")
        else:
            doc.db_set({"status": "Review", "last_error": "Cancellation received after dispatch"})
    elif status == "ORDER_PICKED_UP":
        if fulfillment.fulfillment_type == "Pickup" and fulfillment.status == "Ready":
            fulfillment._transition("Picked Up", automatic=True)
        elif fulfillment.fulfillment_type == "Delivery" and fulfillment.status == "Ready":
            fulfillment._transition("Out for Delivery", automatic=True)


def recover_pending_orders():
    rows = frappe.get_all(
        "PedidosYa Order",
        filters={"status": ["in", ["Received", "Error"]], "attempts": ["<", 10], "table_order": ["is", "not set"]},
        pluck="name",
        limit_page_length=100,
    )
    for name in rows:
        _queue(
            "restaurant_management.integrations.pedidosya.service.process_order",
            job_id=f"pedidosya-recovery:{name}",
            name=name,
        )
    imported = frappe.get_all(
        "PedidosYa Order",
        filters={"status": "Imported", "table_order": ["is", "set"]},
        pluck="name",
        limit_page_length=100,
    )
    for name in imported:
        _queue(
            "restaurant_management.integrations.pedidosya.service.accept_order_automatic",
            job_id=f"pedidosya-accept-recovery:{name}",
            name=name,
        )

    pending_callbacks = frappe.get_all(
        "PedidosYa Order",
        filters={"status": ["in", ["Accepted", "Rejected"]]},
        fields=[
            "name", "settings", "status", "accepted_callback_url", "accepted_notified",
            "rejected_callback_url", "rejected_notified", "rejection_reason", "rejection_message",
        ],
        limit_page_length=100,
    )
    for row in pending_callbacks:
        event = None
        if row.status == "Accepted" and row.accepted_callback_url and not row.accepted_notified:
            settings_flow = frappe.db.get_value("PedidosYa Integration Settings", row.settings, "integration_flow")
            event = "accepted" if settings_flow == "Direct" else None
        elif row.status == "Rejected" and row.rejected_callback_url and not row.rejected_notified:
            event = "rejected"
        if event:
            _queue(
                "restaurant_management.integrations.pedidosya.service.send_callback",
                job_id=f"pedidosya-{event}-recovery:{row.name}",
                name=row.name,
                event=event,
                reason=row.rejection_reason if event == "rejected" else None,
                message=row.rejection_message if event == "rejected" else None,
            )

    prepared = frappe.get_all(
        "PedidosYa Order",
        filters={"prepared_notified": 0, "prepared_callback_url": ["is", "set"], "fulfillment": ["is", "set"]},
        fields=["name", "fulfillment"],
        limit_page_length=100,
    )
    for row in prepared:
        if frappe.db.get_value("Restaurant Fulfillment", row.fulfillment, "status") in {
            "Ready", "Assigned", "Out for Delivery", "Delivered", "Picked Up"
        }:
            notify_prepared_by_fulfillment(row.fulfillment)

    picked_up = frappe.get_all(
        "PedidosYa Order",
        filters={"picked_up_notified": 0, "picked_up_callback_url": ["is", "set"], "fulfillment": ["is", "set"]},
        fields=["name", "fulfillment"],
        limit_page_length=100,
    )
    for row in picked_up:
        fulfillment = frappe.db.get_value(
            "Restaurant Fulfillment", row.fulfillment, ["status", "delivery_provider"], as_dict=True
        )
        if fulfillment and (
            fulfillment.status == "Picked Up"
            or (fulfillment.status == "Out for Delivery" and fulfillment.delivery_provider == "Restaurant")
        ):
            notify_picked_up_by_fulfillment(row.fulfillment)


def accept_order_automatic(name):
    return _accept(name, automatic=True)
