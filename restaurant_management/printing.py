"""Durable, company-scoped restaurant printing.

PDF rendering remains available through ``silent_print``; fiscal invoices and pre-accounts may
use native ESC/POS. This module owns routing and the auditable delivery lifecycle.
"""

from base64 import b64encode
import hashlib
import re

import frappe
from frappe import _
from frappe.utils import add_to_date, cint, now_datetime

from restaurant_management.restaurant_management.company_settings import (
	get_restaurant_settings,
)
from restaurant_management.thermal_print import (
	build_pos_invoice_escpos,
	build_table_order_account_escpos,
)


CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
ROUTE_TYPES = {"INVOICE", "ACCOUNT", "ORDER", "KITCHEN"}
TERMINAL_STATUSES = {"Accepted by HWB", "Confirmed Printed", "Cancelled"}
BRIDGE_STATES = {"idle", "connecting", "open", "closed", "failed"}


def _authenticated_user():
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)
	return frappe.session.user


def _validate_client_id(client_id):
	client_id = str(client_id or "").strip()
	if not CLIENT_ID_PATTERN.fullmatch(client_id):
		frappe.throw(_("Invalid print station client identifier"))
	return client_id


def _station_is_active(station, now=None):
	now = now or now_datetime()
	return bool(
		station.get("client_id")
		and station.get("lease_expires_on")
		and station.lease_expires_on >= now
	)


def _get_station(station_name, client_id=None, require_lease=False):
	user = _authenticated_user()
	station = frappe.get_doc("Restaurant Print Station", station_name)
	if not station.enabled:
		frappe.throw(_("Print station is disabled"))
	if station.station_user != user:
		frappe.throw(_("This user is not assigned to the print station"), frappe.PermissionError)
	if client_id is not None:
		client_id = _validate_client_id(client_id)
		if require_lease and station.client_id != client_id:
			frappe.throw(_("The print station lease belongs to another browser"), frappe.PermissionError)
		if require_lease and (
			not station.lease_expires_on or station.lease_expires_on < now_datetime()
		):
			frappe.throw(_("The print station lease has expired"))
	return station


def _get_route(settings, route_type, production_center=None):
	route_type = str(route_type or "").upper()
	if route_type not in ROUTE_TYPES:
		frappe.throw(_("Unsupported restaurant print route"))

	candidates = [
		route for route in settings.get("print_routes", [])
		if route.enabled and route.document_type == route_type
	]
	if route_type == "KITCHEN":
		exact = [r for r in candidates if r.production_center == production_center]
		candidates = exact or [r for r in candidates if not r.production_center]
	else:
		candidates = [r for r in candidates if not r.production_center]

	if not candidates:
		return None
	if len(candidates) > 1:
		frappe.throw(_("More than one print route matches {0}").format(route_type))
	return candidates[0]


def enqueue_print(
	source_doctype,
	source_name,
	route_type,
	company=None,
	production_center=None,
	event_key=None,
	requested_by=None,
	require_route=True,
	coalesce_pending=False,
):
	"""Create at most one job for the same source, route and business event."""
	source = frappe.get_doc(source_doctype, source_name)
	company = company or source.get("company")
	if not company:
		frappe.throw(_("The print source must belong to a company"))
	if source.get("company") and source.company != company:
		frappe.throw(_("The print source belongs to another company"))

	settings = get_restaurant_settings(company=company)
	route = _get_route(settings, route_type, production_center)
	if not route:
		if require_route:
			frappe.throw(_("Configure an enabled {0} print route for {1}").format(route_type, company))
		return {"queued": False, "configured": False, "route_type": route_type}

	station = frappe.db.get_value(
		"Restaurant Print Station",
		route.station,
		["company", "enabled", "client_id", "lease_expires_on"],
		as_dict=True,
	)
	if not station or not station.enabled or station.company != company:
		frappe.throw(_("The configured print station is unavailable or belongs to another company"))
	station_active = _station_is_active(station)
	if coalesce_pending:
		pending = frappe.get_all(
			"Restaurant Print Job",
			filters={
				"source_doctype": source_doctype,
				"source_name": source_name,
				"station": route.station,
				"route_type": route.document_type,
				"status": ["in", ["Pending", "Sending"]],
			},
			pluck="name",
			order_by="creation asc",
			limit_page_length=1,
		)
		if pending:
			return {
				"queued": True,
				"configured": True,
				"job": pending[0],
				"duplicate": True,
				"print_type": route.print_type,
				"station": route.station,
				"station_active": station_active,
			}

	key_source = "|".join([
		source_doctype,
		source_name,
		route.name,
		str(event_key or "default"),
	])
	idempotency_key = hashlib.sha256(key_source.encode()).hexdigest()
	existing = frappe.db.get_value("Restaurant Print Job", {"idempotency_key": idempotency_key}, "name")
	if existing:
		return {
			"queued": True,
			"configured": True,
			"job": existing,
			"duplicate": True,
			"print_type": route.print_type,
			"station": route.station,
			"station_active": station_active,
		}

	job = frappe.get_doc({
		"doctype": "Restaurant Print Job",
		"company": company,
		"station": route.station,
		"route_type": route.document_type,
		"production_center": route.production_center,
		"source_doctype": source_doctype,
		"source_name": source_name,
		"print_format": route.print_format,
		"print_type": route.print_type,
		"transport_mode": route.transport_mode or "PDF",
		"copies": max(1, cint(route.copies)),
		"status": "Pending",
		"attempt_count": 0,
		"idempotency_key": idempotency_key,
		"requested_by": requested_by or frappe.session.user,
		"requested_on": now_datetime(),
	})
	job.insert(ignore_permissions=True)
	frappe.publish_realtime(
		"restaurant_print_job",
		{"job": job.name, "station": job.station, "status": job.status},
		user=frappe.db.get_value("Restaurant Print Station", job.station, "station_user"),
		after_commit=True,
	)
	return {
		"queued": True,
		"configured": True,
		"job": job.name,
		"duplicate": False,
		"print_type": route.print_type,
		"station": route.station,
		"station_active": station_active,
	}


@frappe.whitelist(methods=["POST"])
def queue_invoice_print(invoice_name, request_id=None):
	"""Queue an invoice after issue or as an explicit, idempotent manual reprint."""
	_authenticated_user()
	invoice = frappe.get_doc("POS Invoice", invoice_name)
	invoice.check_permission("print")
	event_key = "electronic-invoice"
	if request_id:
		request_id = str(request_id).strip()
		if not CLIENT_ID_PATTERN.fullmatch(request_id):
			frappe.throw(_("Invalid manual print request identifier"), frappe.ValidationError)
		event_key = f"manual-invoice:{request_id}"
	return enqueue_print(
		"POS Invoice", invoice.name, "INVOICE", company=invoice.company,
		event_key=event_key,
		coalesce_pending=bool(request_id),
	)


@frappe.whitelist()
def update_pos_invoice_ce_and_queue_print(
	company,
	invoice,
	doctype,
	estado_sunat,
	cadena_para_codigo_qr,
	codigo_hash,
	enlace_del_pdf,
):
	"""Persist the electronic result and guarantee its automatic print job.

	The electronic provider commits the accepted fields directly with SQL, so
	POS Invoice document hooks do not run.  This override keeps that integration
	intact and creates the idempotent print job in the same server request.
	"""
	from ovenube_peru.nubefact_integration.facturacion_electronica import (
		update_pos_invoice_ce,
	)

	result = update_pos_invoice_ce(
		company,
		invoice,
		doctype,
		estado_sunat,
		cadena_para_codigo_qr,
		codigo_hash,
		enlace_del_pdf,
	)
	print_result = None
	accepted = str(estado_sunat or "").strip().lower() in {
		"aceptado",
		"accepted",
	}
	if doctype == "POS Invoice" and accepted and str(codigo_hash or "").strip():
		try:
			print_result = queue_invoice_print(invoice)
		except Exception:
			frappe.log_error(
				title=_("Automatic electronic receipt printing failed"),
				message=frappe.get_traceback(),
			)
			print_result = {
				"queued": False,
				"error": _(
					"The electronic receipt was accepted, but it could not be queued for printing"
				),
			}

	return {
		"updated": True,
		"provider_result": result,
		"codigo_hash": codigo_hash,
		"print_queue": print_result,
	}


@frappe.whitelist(methods=["GET"])
def get_station_bootstrap():
	user = _authenticated_user()
	company = frappe.defaults.get_user_default("company", user=user)
	filters = {"station_user": user, "enabled": 1}
	if company:
		filters["company"] = company
	stations = frappe.get_all(
		"Restaurant Print Station",
		filters=filters,
		fields=[
			"name", "station_name", "company", "bridge_protocol", "lease_seconds", "last_seen",
			"hw_bridge_version", "bridge_state", "client_id", "lease_expires_on",
		],
		order_by="station_name asc",
	)
	for station in stations:
		station.active = _station_is_active(station)
		station.pop("client_id", None)
	return {"company": company, "stations": stations, "bridge_url": "ws://127.0.0.1:12212"}


@frappe.whitelist(methods=["POST"])
def heartbeat(station, client_id, hw_bridge_version=None, bridge_state=None):
	client_id = _validate_client_id(client_id)
	doc = _get_station(station)
	now = now_datetime()
	# A live lease cannot be silently stolen by a second browser tab.
	if doc.client_id and doc.client_id != client_id and doc.lease_expires_on and doc.lease_expires_on >= now:
		frappe.throw(_("This print station is active in another browser"))
	expires = add_to_date(now, seconds=max(15, cint(doc.lease_seconds or 45)))
	bridge_state = str(bridge_state or "idle").strip().lower()
	if bridge_state not in BRIDGE_STATES:
		bridge_state = "failed"
	frappe.db.set_value(
		"Restaurant Print Station",
		doc.name,
		{
			"last_seen": now,
			"client_id": client_id,
			"hw_bridge_version": str(hw_bridge_version or "")[:140],
			"bridge_state": bridge_state,
			"lease_expires_on": expires,
		},
		update_modified=False,
	)
	return {"station": doc.name, "lease_expires_on": expires}


@frappe.whitelist(methods=["POST"])
def disconnect_station(station, client_id=None, force=False):
	"""Release the caller's assigned company station lease.

	An explicit forced release is used when the same cashier lost the browser
	client identifier after logging out or closing the console.  It remains
	scoped to both the assigned station user and the user's current company.
	"""
	if cint(force):
		doc = _get_station(station)
		user_company = frappe.defaults.get_user_default(
			"company", user=frappe.session.user
		)
		if not user_company:
			frappe.throw(
				_("Set a default Company before disconnecting the print station")
			)
		if doc.company != user_company:
			frappe.throw(
				_("The print station belongs to another company"),
				frappe.PermissionError,
			)
	else:
		doc = _get_station(station, client_id, require_lease=True)
	frappe.db.set_value(
		"Restaurant Print Station",
		doc.name,
		{
			"client_id": None,
			"lease_expires_on": None,
			"bridge_state": "idle",
		},
		update_modified=False,
	)
	frappe.publish_realtime(
		"restaurant_print_station",
		{"station": doc.name, "company": doc.company, "active": False},
		user=doc.station_user,
		after_commit=True,
	)
	return {"station": doc.name, "company": doc.company, "active": False}


@frappe.whitelist(methods=["POST"])
def claim_jobs(station, client_id, limit=3):
	doc = _get_station(station, client_id, require_lease=True)
	limit = min(10, max(1, cint(limit)))
	stale_before = add_to_date(now_datetime(), seconds=-(max(15, cint(doc.lease_seconds or 45)) * 2))
	# A station crash makes delivery unknowable; require review rather than duplicate a ticket.
	frappe.db.sql(
		"""update `tabRestaurant Print Job`
		set status='Ambiguous', last_error=%s
		where station=%s and status='Sending' and claimed_on < %s""",
		(_("Station lease expired during delivery; verify the printer"), doc.name, stale_before),
	)
	rows = frappe.db.sql(
		"""select name from `tabRestaurant Print Job`
		where station=%s and status='Pending'
		order by creation asc limit %s for update""",
		(doc.name, limit),
		as_dict=True,
	)
	now = now_datetime()
	jobs = []
	for row in rows:
		frappe.db.set_value(
			"Restaurant Print Job",
			row.name,
			{
				"status": "Sending",
				"attempt_count": frappe.db.get_value("Restaurant Print Job", row.name, "attempt_count") + 1,
				"claimed_by": frappe.session.user,
				"client_id": client_id,
				"claimed_on": now,
				"last_error": None,
			},
			update_modified=False,
		)
		jobs.append(row.name)
	return jobs


def _get_claimed_job(job_name, client_id):
	client_id = _validate_client_id(client_id)
	job = frappe.get_doc("Restaurant Print Job", job_name)
	_get_station(job.station, client_id, require_lease=True)
	if job.client_id != client_id or job.claimed_by != frappe.session.user:
		frappe.throw(_("The print job is claimed by another station session"), frappe.PermissionError)
	return job


@frappe.whitelist(methods=["POST"])
def render_job(job, client_id):
	doc = _get_claimed_job(job, client_id)
	if doc.status != "Sending":
		frappe.throw(_("Only Sending jobs can be rendered"))

	if doc.transport_mode == "ESC/POS" and doc.route_type in {"INVOICE", "ACCOUNT"}:
		source = frappe.get_doc(doc.source_doctype, doc.source_name)
		company_tax_id = frappe.db.get_value("Company", source.company, "tax_id")
		if doc.route_type == "INVOICE":
			tip = frappe.db.get_value(
				"Restaurant Tip",
				{
					"pos_invoice": source.name,
					"status": ["in", ["Collected", "Settled"]],
				},
				["amount", "mode_of_payment"],
				as_dict=True,
			)
			raw = build_pos_invoice_escpos(
				source,
				company_tax_id=company_tax_id,
				tip=tip,
				copies=max(1, cint(doc.copies)),
			)
		else:
			waiter_user = source.get("cambio_mozo") or source.owner
			waiter_name = frappe.db.get_value("User", waiter_user, "full_name")
			raw = build_table_order_account_escpos(
				source,
				company_tax_id=company_tax_id,
				waiter_name=waiter_name,
				copies=max(1, cint(doc.copies)),
			)
		return {
			"id": doc.name,
			"job_id": doc.name,
			"type": doc.print_type,
			"print_type": doc.print_type,
			"url": f"{doc.name}.bin",
			"raw_content": b64encode(raw).decode("ascii"),
			"qty": 1,
			"transport_mode": "ESC/POS",
		}

	create_pdf = frappe.get_attr("silent_print.utils.service.create_pdf")
	rendered = create_pdf(doc.source_doctype, doc.source_name, doc.print_format)
	return {
		"id": doc.name,
		"job_id": doc.name,
		"type": doc.print_type,
		"print_type": doc.print_type,
		"url": f"{doc.name}.pdf",
		"file_content": rendered["pdf_base64"],
		"qty": max(1, cint(doc.copies)),
		"transport_mode": "PDF",
	}


@frappe.whitelist(methods=["POST"])
def acknowledge_job(job, client_id, success=0, printer=None, message=None, ambiguous=0):
	doc = _get_claimed_job(job, client_id)
	if doc.status != "Sending":
		return {"job": doc.name, "status": doc.status}
	if cint(ambiguous):
		status = "Ambiguous"
	elif cint(success):
		status = "Accepted by HWB"
	else:
		status = "Failed"
	values = {
		"status": status,
		"printer_name": str(printer or "")[:140],
		"response_message": str(message or "")[:1000],
		"last_error": str(message or "")[:1000] if status in {"Failed", "Ambiguous"} else None,
	}
	if status == "Accepted by HWB":
		values["accepted_on"] = now_datetime()
	frappe.db.set_value("Restaurant Print Job", doc.name, values, update_modified=False)
	return {"job": doc.name, "status": status}


@frappe.whitelist(methods=["POST"])
def release_job(job, client_id, message=None):
	"""Return a job to Pending only when no bytes reached Hardware Bridge."""
	doc = _get_claimed_job(job, client_id)
	if doc.status == "Sending":
		frappe.db.set_value(
			"Restaurant Print Job", doc.name,
			{"status": "Pending", "last_error": str(message or "Bridge offline")[:1000]},
			update_modified=False,
		)
	return {"job": doc.name, "status": "Pending"}


@frappe.whitelist(methods=["POST"])
def retry_job(job):
	_authenticated_user()
	doc = frappe.get_doc("Restaurant Print Job", job)
	if doc.status not in {"Failed", "Ambiguous"}:
		frappe.throw(_("Only Failed or Ambiguous jobs can be retried"))
	is_admin = bool({"resto_admin", "System Manager"}.intersection(frappe.get_roles()))
	is_station_cashier = (
		doc.status == "Failed"
		and frappe.db.get_value("Restaurant Print Station", doc.station, "station_user")
		== frappe.session.user
	)
	if not (is_admin or is_station_cashier):
		frappe.throw(
			_("Only a restaurant administrator can retry an ambiguous print job"),
			frappe.PermissionError,
		)
	retry = frappe.copy_doc(doc)
	retry.status = "Pending"
	retry.attempt_count = 0
	retry.idempotency_key = hashlib.sha256(
		"{0}|retry|{1}".format(doc.idempotency_key, frappe.generate_hash(length=16)).encode()
	).hexdigest()
	retry.requested_by = frappe.session.user
	retry.requested_on = now_datetime()
	retry.claimed_by = None
	retry.client_id = None
	retry.claimed_on = None
	retry.accepted_on = None
	retry.printer_name = None
	retry.response_message = None
	retry.last_error = None
	retry.insert(ignore_permissions=True)
	frappe.publish_realtime(
		"restaurant_print_job", {"job": retry.name, "station": retry.station, "status": retry.status},
		user=frappe.db.get_value("Restaurant Print Station", retry.station, "station_user"), after_commit=True,
	)
	return {"job": retry.name, "status": retry.status, "retried_from": doc.name}


def _can_operate_job(doc):
	"""Allow administrators or the cashier assigned to this job's station."""
	if {"resto_admin", "System Manager"}.intersection(frappe.get_roles()):
		return True
	return (
		frappe.db.get_value("Restaurant Print Station", doc.station, "station_user")
		== frappe.session.user
	)


@frappe.whitelist(methods=["POST"])
def resolve_job(job, action, note=None):
	"""Close an ambiguous or failed print incident without deleting its audit trail."""
	_authenticated_user()
	doc = frappe.get_doc("Restaurant Print Job", job)
	if not _can_operate_job(doc):
		frappe.throw(
			_("Only the assigned print station operator or a restaurant administrator can resolve this job"),
			frappe.PermissionError,
		)

	action = str(action or "").strip().lower()
	note = str(note or "").strip()[:1000]
	if action == "confirm_printed":
		if doc.status != "Ambiguous":
			frappe.throw(_("Only an Ambiguous job can be confirmed as printed"))
		status = "Confirmed Printed"
		default_note = _("Physically confirmed at the printer")
	elif action == "discard":
		if doc.status not in {"Failed", "Ambiguous"}:
			frappe.throw(_("Only Failed or Ambiguous jobs can be discarded"))
		if not note:
			frappe.throw(_("Enter a reason for discarding the print job"), frappe.ValidationError)
		status = "Cancelled"
		default_note = note
	else:
		frappe.throw(_("Unsupported print job resolution"), frappe.ValidationError)

	values = {
		"status": status,
		"resolved_by": frappe.session.user,
		"resolved_on": now_datetime(),
		"resolution_note": note or default_note,
		"last_error": None,
	}
	if status == "Confirmed Printed":
		values["accepted_on"] = now_datetime()
	frappe.db.set_value("Restaurant Print Job", doc.name, values, update_modified=False)
	return {"job": doc.name, "status": status}


@frappe.whitelist(methods=["GET"])
def station_jobs(station, limit=30):
	doc = _get_station(station)
	return frappe.get_all(
		"Restaurant Print Job",
		filters={"station": doc.name},
		fields=["name", "route_type", "source_name", "status", "attempt_count", "requested_on", "printer_name", "last_error"],
		order_by="creation desc",
		limit_page_length=min(100, max(1, cint(limit))),
	)
