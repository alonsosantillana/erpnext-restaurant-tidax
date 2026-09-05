"""Recoverable electronic submission for restaurant POS invoices."""

from __future__ import annotations

import re

import frappe
from frappe import _
from frappe.permissions import has_permission
from frappe.utils import add_to_date, cint, get_datetime, now_datetime
from frappe.utils.file_lock import LockTimeoutError
from frappe.utils.synchronization import filelock

from restaurant_management.restaurant_management.company_settings import (
	get_restaurant_payment_permissions,
)


ELECTRONIC_MODE = "Electrónica"
STATUS_QUEUED = "Queued"
STATUS_SENDING = "Sending"
STATUS_ACCEPTED = "Accepted"
STATUS_RETRY_REQUIRED = "Retry Required"
STATUS_REJECTED = "Rejected"
RETRYABLE_STATUSES = (STATUS_QUEUED, STATUS_SENDING, STATUS_RETRY_REQUIRED)
MAX_AUTOMATIC_ATTEMPTS = 3
STALE_SENDING_MINUTES = 3
JOB_PATH = "restaurant_management.electronic_invoice.process_queued_pos_invoice_electronic"


def _status_values(invoice_name, status, *, error=None, increment_attempts=False):
	values = {
		"restaurant_electronic_status": status,
		"restaurant_electronic_last_error": error,
	}
	if status == STATUS_SENDING:
		values["restaurant_electronic_last_attempt"] = now_datetime()
	if increment_attempts:
		values["restaurant_electronic_attempts"] = cint(
			frappe.db.get_value(
				"POS Invoice", invoice_name, "restaurant_electronic_attempts"
			)
		) + 1
	return values


def _set_status(invoice_name, status, *, error=None, increment_attempts=False):
	"""Persist only sanitized lifecycle information, never provider payloads or secrets."""
	frappe.db.set_value(
		"POS Invoice",
		invoice_name,
		_status_values(
			invoice_name,
			status,
			error=error,
			increment_attempts=increment_attempts,
		),
		update_modified=False,
	)


def _safe_provider_failure(provider_result):
	classification = str(provider_result.get("nubefact_classification") or "unconfirmed").strip()
	code = str(provider_result.get("codigo") or "").strip()
	detail = f" ({classification}"
	if code:
		detail += f", código {code}"
	detail += ")"
	return _("Nubefact no confirmó el comprobante") + detail


def _is_electronic(invoice):
	return (
		cint(invoice.docstatus) == 1
		and str(invoice.get("comprobante_electronico_manual") or "").strip() == ELECTRONIC_MODE
	)


def _get_linked_order(invoice_name):
	return frappe.db.get_value(
		"Table Order",
		{"link_invoice": invoice_name},
		["pos_profile", "owner", "cambio_mozo"],
		as_dict=True,
	)


def _check_user_access(invoice):
	if frappe.session.user == "Guest":
		frappe.throw(_("Authentication required"), frappe.AuthenticationError)
	if has_permission("POS Invoice", "write", invoice, raise_exception=False):
		return

	order = _get_linked_order(invoice.name)
	permissions = get_restaurant_payment_permissions(
		order.pos_profile if order else invoice.pos_profile,
		order_owner=(order.cambio_mozo or order.owner) if order else invoice.owner,
	)
	if not permissions.can_pay:
		frappe.throw(
			_("Not permitted to process this electronic invoice"),
			frappe.PermissionError,
		)


def _job_id(invoice_name):
	return "restaurant-electronic-" + re.sub(r"[^A-Za-z0-9_.-]", "_", invoice_name)


def enqueue_pos_invoice_electronic(
	invoice_name,
	*,
	enqueue_after_commit=False,
	force=False,
):
	"""Mark and enqueue one electronic invoice without coupling it to the browser request."""
	invoice = frappe.get_doc("POS Invoice", invoice_name)
	if not _is_electronic(invoice):
		return {"queued": False, "reason": "not_submitted_electronic_invoice"}
	if str(invoice.get("codigo_hash_sunat") or "").strip():
		_set_status(invoice.name, STATUS_ACCEPTED)
		return {"queued": False, "processed": True, "status": STATUS_ACCEPTED}

	status = str(invoice.get("restaurant_electronic_status") or "").strip()
	attempts = cint(invoice.get("restaurant_electronic_attempts"))
	if status == STATUS_REJECTED and not force:
		return {"queued": False, "reason": "rejected", "status": status}
	if attempts >= MAX_AUTOMATIC_ATTEMPTS and not force:
		return {"queued": False, "reason": "attempt_limit", "status": status}

	_set_status(invoice.name, STATUS_QUEUED)
	job = frappe.enqueue(
		JOB_PATH,
		queue="default",
		timeout=150,
		job_id=_job_id(invoice.name),
		deduplicate=True,
		enqueue_after_commit=enqueue_after_commit,
		invoice_name=invoice.name,
	)
	return {
		"queued": True,
		"invoice": invoice.name,
		"status": STATUS_QUEUED,
		"job": getattr(job, "id", None),
	}


def _synchronize_pos_invoice_electronic(invoice_name):
	invoice = frappe.get_doc("POS Invoice", invoice_name)
	if not _is_electronic(invoice):
		return {"processed": False, "reason": "not_submitted_electronic_invoice"}
	if str(invoice.get("codigo_hash_sunat") or "").strip():
		_set_status(invoice.name, STATUS_ACCEPTED)
		frappe.db.commit()
		return {"processed": True, "invoice": invoice.name, "status": STATUS_ACCEPTED}

	_set_status(invoice.name, STATUS_SENDING, increment_attempts=True)
	frappe.db.commit()

	try:
		from ovenube_peru.nubefact_integration.facturacion_electronica import (
			consult_document,
			send_document,
		)

		provider_result = consult_document(
			invoice.company, invoice.name, "POS Invoice"
		) or {}
		classification = str(
			provider_result.get("nubefact_classification") or ""
		).strip().lower()
		provider_code = str(provider_result.get("codigo") or "").strip()
		if classification == "not_found" or provider_code == "24":
			provider_result = send_document(
				invoice.company, invoice.name, "POS Invoice"
			) or {}

		codigo_hash = str(provider_result.get("codigo_hash") or "").strip()
		if not codigo_hash:
			classification = str(
				provider_result.get("nubefact_classification") or ""
			).strip().lower()
			status = STATUS_REJECTED if classification == "rejected" else STATUS_RETRY_REQUIRED
			error = _safe_provider_failure(provider_result)
			_set_status(invoice.name, status, error=error)
			frappe.db.commit()
			return {
				"processed": False,
				"invoice": invoice.name,
				"status": status,
				"message": error,
			}

		from restaurant_management.printing import update_pos_invoice_ce_and_queue_print

		update_result = update_pos_invoice_ce_and_queue_print(
			invoice.company,
			invoice.name,
			"POS Invoice",
			"Aceptado",
			provider_result.get("cadena_para_codigo_qr") or "",
			codigo_hash,
			provider_result.get("enlace_del_pdf") or "",
		)
		_set_status(invoice.name, STATUS_ACCEPTED)
		frappe.db.commit()
		return {
			"processed": True,
			"invoice": invoice.name,
			"status": STATUS_ACCEPTED,
			"print_queue": update_result.get("print_queue"),
		}
	except Exception as error:
		frappe.db.rollback()
		safe_error = _("No se pudo confirmar el comprobante con Nubefact; se reintentará")
		_set_status(invoice.name, STATUS_RETRY_REQUIRED, error=safe_error)
		frappe.log_error(
			title="NUBEFACT: emisión POS pendiente",
			message=f"POS Invoice {invoice.name}; clase: {type(error).__name__}.",
		)
		frappe.db.commit()
		return {
			"processed": False,
			"invoice": invoice.name,
			"status": STATUS_RETRY_REQUIRED,
			"message": safe_error,
		}


def synchronize_pos_invoice_electronic(invoice_name):
	"""Consult-before-send under a per-document lock to prevent duplicate emission."""
	lock_name = _job_id(invoice_name)
	try:
		with filelock(lock_name, timeout=0):
			return _synchronize_pos_invoice_electronic(invoice_name)
	except LockTimeoutError:
		return {
			"processed": False,
			"invoice": invoice_name,
			"status": STATUS_SENDING,
			"message": _("El comprobante ya se está procesando"),
		}


def process_queued_pos_invoice_electronic(invoice_name):
	return synchronize_pos_invoice_electronic(invoice_name)


def get_retryable_pos_invoice_names(limit=50, now=None):
	now = now or now_datetime()
	rows = frappe.get_all(
		"POS Invoice",
		filters={
			"docstatus": 1,
			"comprobante_electronico_manual": ELECTRONIC_MODE,
			"restaurant_electronic_status": ["in", RETRYABLE_STATUSES],
			"restaurant_electronic_attempts": ["<", MAX_AUTOMATIC_ATTEMPTS],
			"codigo_hash_sunat": ["is", "not set"],
		},
		fields=[
			"name",
			"restaurant_electronic_status",
			"restaurant_electronic_last_attempt",
		],
		order_by="creation asc",
		limit_page_length=max(1, min(cint(limit), 100)),
	)
	stale_before = add_to_date(now, minutes=-STALE_SENDING_MINUTES)
	return [
		row.name
		for row in rows
		if row.restaurant_electronic_status != STATUS_SENDING
		or not row.restaurant_electronic_last_attempt
		or get_datetime(row.restaurant_electronic_last_attempt) <= stale_before
	]


def enqueue_pending_pos_invoice_electronic():
	"""Recover only invoices explicitly marked by this restaurant workflow."""
	names = get_retryable_pos_invoice_names()
	for invoice_name in names:
		enqueue_pos_invoice_electronic(invoice_name)
	return {"selected": len(names), "invoices": names}


@frappe.whitelist(methods=["POST"])
def retry_pos_invoice_electronic(invoice_name):
	invoice = frappe.get_doc("POS Invoice", invoice_name)
	_check_user_access(invoice)
	return enqueue_pos_invoice_electronic(invoice.name, force=True)


@frappe.whitelist()
def get_pos_invoice_electronic_status(invoice_name):
	invoice = frappe.get_doc("POS Invoice", invoice_name)
	_check_user_access(invoice)
	return {
		"invoice": invoice.name,
		"status": invoice.get("restaurant_electronic_status") or "",
		"processed": bool(str(invoice.get("codigo_hash_sunat") or "").strip()),
		"attempts": cint(invoice.get("restaurant_electronic_attempts")),
		"message": invoice.get("restaurant_electronic_last_error") or "",
	}
