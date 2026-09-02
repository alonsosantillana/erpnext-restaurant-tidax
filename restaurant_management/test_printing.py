from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.printing import (
	_get_route,
	_station_is_active,
	_validate_client_id,
	disconnect_station,
	queue_invoice_print,
	queue_order_print,
	render_job,
	resolve_job,
	update_pos_invoice_ce_and_queue_print,
)
from frappe.utils import add_to_date, now_datetime


class TestRestaurantPrinting(FrappeTestCase):
	def test_station_activity_requires_a_live_client_lease(self):
		now = now_datetime()
		self.assertTrue(_station_is_active(frappe._dict(
			client_id="browser-1",
			lease_expires_on=add_to_date(now, seconds=10),
		), now))
		self.assertFalse(_station_is_active(frappe._dict(
			client_id="browser-1",
			lease_expires_on=add_to_date(now, seconds=-1),
		), now))

	def test_client_id_rejects_untrusted_characters(self):
		self.assertRaises(frappe.ValidationError, _validate_client_id, "tab<script>")

	def test_route_prefers_exact_production_center(self):
		settings = frappe._dict(print_routes=[
			frappe._dict(enabled=1, document_type="KITCHEN", production_center=None, name="fallback"),
			frappe._dict(enabled=1, document_type="KITCHEN", production_center="P3", name="exact"),
		])
		self.assertEqual(_get_route(settings, "KITCHEN", "P3").name, "exact")

	def test_optional_route_reports_not_configured(self):
		settings = frappe._dict(print_routes=[])
		self.assertIsNone(_get_route(settings, "ORDER"))

	@patch("restaurant_management.printing.frappe.get_attr")
	@patch("restaurant_management.printing._get_claimed_job")
	def test_rendered_job_uses_pdf_filename_for_hardware_bridge(
		self, get_claimed_job, get_attr
	):
		get_claimed_job.return_value = frappe._dict(
			name="RPJ-TEST-00001",
			status="Sending",
			source_doctype="POS Invoice",
			source_name="PINV-00001",
			print_format="Return POS Invoice",
			print_type="INVOICE",
			copies=1,
			route_type="INVOICE",
			transport_mode="PDF",
		)
		get_attr.return_value.return_value = {"pdf_base64": "UERG"}

		payload = render_job("RPJ-TEST-00001", "browser-1")

		self.assertEqual(payload["url"], "RPJ-TEST-00001.pdf")
		self.assertEqual(payload["file_content"], "UERG")

	def test_disconnect_releases_only_the_claimed_station(self):
		station = frappe._dict(
			name="Test Station", company="Test Company", station_user="cashier.com"
		)
		with (
			patch("restaurant_management.printing._get_station", return_value=station) as get_station,
			patch("restaurant_management.printing.frappe.db.set_value") as set_value,
			patch("restaurant_management.printing.frappe.publish_realtime"),
		):
			result = disconnect_station(station.name, "browser-1")

		get_station.assert_called_once_with(station.name, "browser-1", require_lease=True)
		values = set_value.call_args.args[2]
		self.assertIsNone(values["client_id"])
		self.assertIsNone(values["lease_expires_on"])
		self.assertEqual(values["bridge_state"], "idle")
		self.assertEqual(result["company"], station.company)

	def test_forced_disconnect_is_scoped_to_the_users_default_company(self):
		station = frappe._dict(
			name="Test Station", company="Test Company", station_user="cashier.com"
		)
		with (
			patch("restaurant_management.printing._get_station", return_value=station) as get_station,
			patch(
				"restaurant_management.printing.frappe.defaults.get_user_default",
				return_value=station.company,
			),
			patch("restaurant_management.printing.frappe.db.set_value") as set_value,
			patch("restaurant_management.printing.frappe.publish_realtime"),
		):
			result = disconnect_station(station.name, force=True)

		get_station.assert_called_once_with(station.name)
		values = set_value.call_args.args[2]
		self.assertIsNone(values["client_id"])
		self.assertIsNone(values["lease_expires_on"])
		self.assertEqual(result["company"], station.company)

	def test_forced_disconnect_rejects_another_company(self):
		station = frappe._dict(
			name="Test Station", company="Other Company", station_user="cashier.com"
		)
		with (
			patch("restaurant_management.printing._get_station", return_value=station),
			patch(
				"restaurant_management.printing.frappe.defaults.get_user_default",
				return_value="Test Company",
			),
			patch("restaurant_management.printing.frappe.db.set_value") as set_value,
		):
			self.assertRaises(
				frappe.PermissionError,
				disconnect_station,
				station.name,
				force=True,
			)

		set_value.assert_not_called()

	def test_ambiguous_job_can_be_confirmed_as_printed(self):
		doc = frappe._dict(name="RPJ-TEST-00002", status="Ambiguous", station="Test Station")
		with (
			patch("restaurant_management.printing._can_operate_job", return_value=True),
			patch("restaurant_management.printing.frappe.get_doc", return_value=doc),
			patch("restaurant_management.printing.frappe.db.set_value") as set_value,
		):
			result = resolve_job(doc.name, "confirm_printed")

		self.assertEqual(result["status"], "Confirmed Printed")
		values = set_value.call_args.args[2]
		self.assertEqual(values["status"], "Confirmed Printed")
		self.assertIsNone(values["last_error"])
		self.assertTrue(values["resolved_by"])
		self.assertTrue(values["resolved_on"])

	def test_failed_job_discard_requires_an_audit_reason(self):
		doc = frappe._dict(name="RPJ-TEST-00003", status="Failed", station="Test Station")
		with (
			patch("restaurant_management.printing._can_operate_job", return_value=True),
			patch("restaurant_management.printing.frappe.get_doc", return_value=doc),
			patch("restaurant_management.printing.frappe.db.set_value") as set_value,
		):
			self.assertRaises(
				frappe.ValidationError, resolve_job, doc.name, "discard", ""
			)

		set_value.assert_not_called()

	@patch("restaurant_management.printing.frappe.session", frappe._dict(user="Guest"))
	def test_guest_cannot_validate_station_client(self):
		from restaurant_management.printing import _authenticated_user

		self.assertRaises(frappe.AuthenticationError, _authenticated_user)

	@patch("restaurant_management.printing.enqueue_print")
	@patch("restaurant_management.printing.frappe.get_doc")
	@patch("restaurant_management.printing._authenticated_user")
	def test_order_print_uses_optional_company_route(
		self, _authenticated_user, get_doc, enqueue_print
	):
		order = Mock()
		order.name = "OR-ADA-2026-00001"
		order.company = "ADDERA PERU SAC"
		get_doc.return_value = order
		enqueue_print.return_value = {"queued": False, "configured": False}

		result = queue_order_print(order.name, "send-1")

		order.check_permission.assert_called_once_with("read")
		enqueue_print.assert_called_once_with(
			"Table Order",
			order.name,
			"ORDER",
			company=order.company,
			event_key="order-send-1",
			require_route=False,
		)
		self.assertFalse(result["queued"])

	@patch("restaurant_management.printing.enqueue_print")
	@patch("restaurant_management.printing.get_restaurant_payment_permissions")
	@patch("restaurant_management.printing.has_permission")
	@patch("restaurant_management.printing.frappe.db.get_value")
	@patch("restaurant_management.printing.frappe.get_doc")
	@patch("restaurant_management.printing._authenticated_user")
	def test_configured_waiter_can_queue_own_invoice(
		self, _authenticated_user, get_doc, get_value, has_permission, payment_permissions, enqueue_print
	):
		invoice = Mock()
		invoice.name = "ACC-PINV-WAITER-1"
		invoice.company = "Test Company"
		has_permission.return_value = False
		get_doc.return_value = invoice
		get_value.return_value = frappe._dict(
			pos_profile="POS Restaurant",
			owner="waiter@example.com",
			cambio_mozo=None,
		)
		payment_permissions.return_value = frappe._dict(can_pay=True)
		enqueue_print.return_value = {"queued": True}

		result = queue_invoice_print(invoice.name)

		self.assertTrue(result["queued"])
		has_permission.assert_called_once_with(
			"POS Invoice", "print", invoice, raise_exception=False
		)
		payment_permissions.assert_called_once_with(
			"POS Restaurant", order_owner="waiter@example.com"
		)

	@patch("restaurant_management.printing.enqueue_print")
	@patch("restaurant_management.printing.has_permission")
	@patch("restaurant_management.printing.frappe.get_doc")
	@patch("restaurant_management.printing._authenticated_user")
	def test_manual_invoice_print_uses_request_specific_event(
		self, _authenticated_user, get_doc, has_permission, enqueue_print
	):
		invoice = Mock()
		invoice.name = "ACC-PINV-0001"
		invoice.company = "Test Company"
		get_doc.return_value = invoice
		has_permission.return_value = True
		enqueue_print.return_value = {"queued": True}

		queue_invoice_print(invoice.name, "manual-request-1")

		has_permission.assert_called_once_with(
			"POS Invoice", "print", invoice, raise_exception=False
		)
		enqueue_print.assert_called_once_with(
			"POS Invoice",
			invoice.name,
			"INVOICE",
			company=invoice.company,
			event_key="manual-invoice:manual-request-1",
			coalesce_pending=True,
		)

	@patch("restaurant_management.printing.enqueue_print")
	@patch("restaurant_management.printing.has_permission")
	@patch("restaurant_management.printing.frappe.get_doc")
	@patch("restaurant_management.printing._authenticated_user")
	def test_automatic_invoice_print_keeps_stable_event(
		self, _authenticated_user, get_doc, has_permission, enqueue_print
	):
		invoice = Mock()
		invoice.name = "ACC-PINV-0002"
		invoice.company = "Test Company"
		get_doc.return_value = invoice
		has_permission.return_value = True

		queue_invoice_print(invoice.name)

		enqueue_print.assert_called_once_with(
			"POS Invoice",
			invoice.name,
			"INVOICE",
			company=invoice.company,
			event_key="electronic-invoice",
			coalesce_pending=False,
		)

	@patch("restaurant_management.printing.queue_invoice_print")
	@patch(
		"ovenube_peru.nubefact_integration.facturacion_electronica.update_pos_invoice_ce"
	)
	def test_electronic_acceptance_persists_and_queues_once(
		self, update_pos_invoice_ce, queue_invoice_print
	):
		queue_invoice_print.return_value = {
			"queued": True,
			"job": "RPJ-TEST-00004",
		}

		result = update_pos_invoice_ce_and_queue_print(
			"Test Company",
			"ACC-PINV-0003",
			"POS Invoice",
			"Aceptado",
			"qr-data",
			"hash-data",
			"https://example.test/invoice.pdf",
		)

		update_pos_invoice_ce.assert_called_once()
		queue_invoice_print.assert_called_once_with("ACC-PINV-0003")
		self.assertTrue(result["updated"])
		self.assertTrue(result["print_queue"]["queued"])

	@patch("restaurant_management.printing.queue_invoice_print")
	@patch(
		"ovenube_peru.nubefact_integration.facturacion_electronica.update_pos_invoice_ce"
	)
	def test_rejected_electronic_receipt_is_not_queued(
		self, update_pos_invoice_ce, queue_invoice_print
	):
		result = update_pos_invoice_ce_and_queue_print(
			"Test Company",
			"ACC-PINV-0004",
			"POS Invoice",
			"Rechazado",
			"",
			"",
			"",
		)

		update_pos_invoice_ce.assert_called_once()
		queue_invoice_print.assert_not_called()
		self.assertIsNone(result["print_queue"])


	@patch("restaurant_management.printing.build_pos_invoice_escpos", return_value=b"RAW")
	@patch("restaurant_management.printing.frappe.db.get_value", return_value=None)
	@patch("restaurant_management.printing.frappe.get_doc")
	@patch("restaurant_management.printing._get_claimed_job")
	def test_invoice_escpos_job_uses_raw_content(
		self, get_claimed_job, get_doc, get_value, build_escpos
	):
		get_claimed_job.return_value = frappe._dict(
			name="RPJ-TEST-ESC-00001",
			status="Sending",
			source_doctype="POS Invoice",
			source_name="BV-BRE1-000012",
			print_format="Restaurant POS Invoice 80mm",
			print_type="INVOICE",
			route_type="INVOICE",
			transport_mode="ESC/POS",
			copies=1,
		)
		invoice = frappe._dict(
			name="BV-BRE1-000012",
			company="Test Company",
		)
		get_doc.return_value = invoice

		payload = render_job("RPJ-TEST-ESC-00001", "browser-1")

		self.assertEqual(payload["url"], "RPJ-TEST-ESC-00001.bin")
		self.assertEqual(payload["raw_content"], "UkFX")
		self.assertNotIn("file_content", payload)
		self.assertEqual(payload["qty"], 1)
		build_escpos.assert_called_once_with(
			invoice,
			company_tax_id=None,
			tip=None,
			copies=1,
		)

	@patch("restaurant_management.printing.build_table_order_account_escpos", return_value=b"ACCOUNT")
	@patch("restaurant_management.printing.frappe.db.get_value", side_effect=[None, "Mozo Uno"])
	@patch("restaurant_management.printing.frappe.get_doc")
	@patch("restaurant_management.printing._get_claimed_job")
	def test_account_escpos_job_uses_raw_content(
		self, get_claimed_job, get_doc, get_value, build_account
	):
		get_claimed_job.return_value = frappe._dict(
			name="RPJ-TEST-ESC-00002",
			status="Sending",
			source_doctype="Table Order",
			source_name="OR-ADA-2026-00014",
			print_format="Order Account",
			print_type="ACCOUNT",
			route_type="ACCOUNT",
			transport_mode="ESC/POS",
			copies=1,
		)
		order = frappe._dict(
			name="OR-ADA-2026-00014",
			company="Test Company",
			owner="waiter@example.com",
		)
		get_doc.return_value = order

		payload = render_job("RPJ-TEST-ESC-00002", "browser-1")

		self.assertEqual(payload["raw_content"], "QUNDT1VOVA==")
		self.assertEqual(payload["transport_mode"], "ESC/POS")
		build_account.assert_called_once_with(
			order, company_tax_id=None, waiter_name="Mozo Uno", copies=1
		)
