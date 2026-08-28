from unittest.mock import Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.printing import (
	_get_route,
	_station_is_active,
	_validate_client_id,
	queue_invoice_print,
	render_job,
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
		)
		get_attr.return_value.return_value = {"pdf_base64": "UERG"}

		payload = render_job("RPJ-TEST-00001", "browser-1")

		self.assertEqual(payload["url"], "RPJ-TEST-00001.pdf")
		self.assertEqual(payload["file_content"], "UERG")

	@patch("restaurant_management.printing.frappe.session", frappe._dict(user="Guest"))
	def test_guest_cannot_validate_station_client(self):
		from restaurant_management.printing import _authenticated_user

		self.assertRaises(frappe.AuthenticationError, _authenticated_user)

	@patch("restaurant_management.printing.enqueue_print")
	@patch("restaurant_management.printing.frappe.get_doc")
	@patch("restaurant_management.printing._authenticated_user")
	def test_manual_invoice_print_uses_request_specific_event(
		self, _authenticated_user, get_doc, enqueue_print
	):
		invoice = Mock()
		invoice.name = "ACC-PINV-0001"
		invoice.company = "Test Company"
		get_doc.return_value = invoice
		enqueue_print.return_value = {"queued": True}

		queue_invoice_print(invoice.name, "manual-request-1")

		invoice.check_permission.assert_called_once_with("print")
		enqueue_print.assert_called_once_with(
			"POS Invoice",
			invoice.name,
			"INVOICE",
			company=invoice.company,
			event_key="manual-invoice:manual-request-1",
			coalesce_pending=True,
		)

	@patch("restaurant_management.printing.enqueue_print")
	@patch("restaurant_management.printing.frappe.get_doc")
	@patch("restaurant_management.printing._authenticated_user")
	def test_automatic_invoice_print_keeps_stable_event(
		self, _authenticated_user, get_doc, enqueue_print
	):
		invoice = Mock()
		invoice.name = "ACC-PINV-0002"
		invoice.company = "Test Company"
		get_doc.return_value = invoice

		queue_invoice_print(invoice.name)

		enqueue_print.assert_called_once_with(
			"POS Invoice",
			invoice.name,
			"INVOICE",
			company=invoice.company,
			event_key="electronic-invoice",
			coalesce_pending=False,
		)
