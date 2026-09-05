from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.electronic_invoice import (
	STATUS_ACCEPTED,
	STATUS_QUEUED,
	STATUS_RETRY_REQUIRED,
	STATUS_SENDING,
	_synchronize_pos_invoice_electronic,
	enqueue_pos_invoice_electronic,
)


def electronic_invoice(**values):
	data = {
		"doctype": "POS Invoice",
		"name": "BV-BRE2-000017",
		"company": "ERPCLOUD SAC",
		"docstatus": 1,
		"comprobante_electronico_manual": "Electrónica",
		"codigo_hash_sunat": "",
		"restaurant_electronic_status": "",
		"restaurant_electronic_attempts": 0,
	}
	data.update(values)
	return frappe._dict(data)


class TestRecoverableElectronicInvoice(FrappeTestCase):
	@patch("restaurant_management.electronic_invoice.frappe.enqueue")
	@patch("restaurant_management.electronic_invoice._set_status")
	@patch("restaurant_management.electronic_invoice.frappe.get_doc")
	def test_enqueue_is_deduplicated_and_runs_after_commit(
		self, get_doc, set_status, enqueue
	):
		get_doc.return_value = electronic_invoice()

		result = enqueue_pos_invoice_electronic(
			"BV-BRE2-000017", enqueue_after_commit=True
		)

		self.assertTrue(result["queued"])
		set_status.assert_called_once_with("BV-BRE2-000017", STATUS_QUEUED)
		enqueue.assert_called_once_with(
			"restaurant_management.electronic_invoice.process_queued_pos_invoice_electronic",
			queue="default",
			timeout=150,
			job_id="restaurant-electronic-BV-BRE2-000017",
			deduplicate=True,
			enqueue_after_commit=True,
			invoice_name="BV-BRE2-000017",
		)

	@patch("restaurant_management.printing.update_pos_invoice_ce_and_queue_print")
	@patch("ovenube_peru.nubefact_integration.facturacion_electronica.send_document")
	@patch("ovenube_peru.nubefact_integration.facturacion_electronica.consult_document")
	@patch("restaurant_management.electronic_invoice.frappe.db.commit")
	@patch("restaurant_management.electronic_invoice._set_status")
	@patch("restaurant_management.electronic_invoice.frappe.get_doc")
	def test_not_found_is_sent_once_and_persisted(
		self, get_doc, set_status, _commit, consult, send, update
	):
		get_doc.return_value = electronic_invoice()
		consult.return_value = {"nubefact_classification": "not_found", "codigo": 24}
		send.return_value = {
			"nubefact_classification": "accepted",
			"codigo_hash": "hash-17",
			"cadena_para_codigo_qr": "qr-17",
			"enlace_del_pdf": "https://example.test/17.pdf",
		}
		update.return_value = {"print_queue": {"queued": True}}

		result = _synchronize_pos_invoice_electronic("BV-BRE2-000017")

		self.assertTrue(result["processed"])
		consult.assert_called_once_with("ERPCLOUD SAC", "BV-BRE2-000017", "POS Invoice")
		send.assert_called_once_with("ERPCLOUD SAC", "BV-BRE2-000017", "POS Invoice")
		update.assert_called_once()
		self.assertEqual(set_status.call_args_list[-1].args, ("BV-BRE2-000017", STATUS_ACCEPTED))

	@patch("restaurant_management.printing.update_pos_invoice_ce_and_queue_print")
	@patch("ovenube_peru.nubefact_integration.facturacion_electronica.send_document")
	@patch("ovenube_peru.nubefact_integration.facturacion_electronica.consult_document")
	@patch("restaurant_management.electronic_invoice.frappe.db.commit")
	@patch("restaurant_management.electronic_invoice._set_status")
	@patch("restaurant_management.electronic_invoice.frappe.get_doc")
	def test_known_remote_invoice_is_not_generated_again(
		self, get_doc, _set_status, _commit, consult, send, update
	):
		get_doc.return_value = electronic_invoice()
		consult.return_value = {
			"nubefact_classification": "accepted",
			"codigo_hash": "existing-hash",
		}
		update.return_value = {"print_queue": {"queued": True}}

		result = _synchronize_pos_invoice_electronic("BV-BRE2-000017")

		self.assertTrue(result["processed"])
		send.assert_not_called()
		update.assert_called_once()

	@patch("restaurant_management.electronic_invoice.frappe.log_error")
	@patch("ovenube_peru.nubefact_integration.facturacion_electronica.consult_document")
	@patch("restaurant_management.electronic_invoice.frappe.db.commit")
	@patch("restaurant_management.electronic_invoice.frappe.db.rollback")
	@patch("restaurant_management.electronic_invoice._set_status")
	@patch("restaurant_management.electronic_invoice.frappe.get_doc")
	def test_timeout_leaves_sanitized_retryable_state(
		self, get_doc, set_status, rollback, _commit, consult, log_error
	):
		get_doc.return_value = electronic_invoice()
		consult.side_effect = TimeoutError("secret provider response")

		result = _synchronize_pos_invoice_electronic("BV-BRE2-000017")

		self.assertFalse(result["processed"])
		self.assertEqual(result["status"], STATUS_RETRY_REQUIRED)
		self.assertNotIn("secret", result["message"])
		rollback.assert_called_once()
		set_status.assert_any_call(
			"BV-BRE2-000017", STATUS_SENDING, increment_attempts=True
		)
		set_status.assert_any_call(
			"BV-BRE2-000017",
			STATUS_RETRY_REQUIRED,
			error=result["message"],
		)
		self.assertNotIn("secret", log_error.call_args.kwargs["message"])

	@patch("restaurant_management.electronic_invoice.frappe.enqueue")
	@patch("restaurant_management.electronic_invoice._set_status")
	@patch("restaurant_management.electronic_invoice.frappe.get_doc")
	def test_existing_hash_is_never_requeued(self, get_doc, set_status, enqueue):
		get_doc.return_value = electronic_invoice(codigo_hash_sunat="existing-hash")

		result = enqueue_pos_invoice_electronic("BV-BRE2-000017")

		self.assertTrue(result["processed"])
		set_status.assert_called_once_with("BV-BRE2-000017", STATUS_ACCEPTED)
		enqueue.assert_not_called()
