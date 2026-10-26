"""Isolated invoice-construction contracts: no site, DB connection or real payment."""

import unittest
from types import MethodType, SimpleNamespace
from unittest.mock import Mock, patch

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import get_bank_cash_account
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice

from restaurant_management.integrations.pedidosya import service
from restaurant_management.restaurant_management.doctype.table_order import table_order as module


def _throw(message, *args, **kwargs):
    raise frappe.ValidationError(message)


def _profile(method="Transferencia", **values):
    return frappe._dict(
        company="TEST COMPANY",
        disabled=0,
        payments=[frappe._dict(mode_of_payment=method, default=1)],
        **values,
    )


class _Row(frappe._dict):
    def as_dict(self):
        return dict(self)

    def set(self, field, value):
        self[field] = value


class TestInvoicePayments(unittest.TestCase):
    def setUp(self):
        frappe.local.db = Mock()
        frappe.local.flags = frappe._dict()
        self.addCleanup(frappe.local.__release_local__)
        self.enterContext(patch.object(frappe, "connect", side_effect=AssertionError("No live DB")))
        self.enterContext(patch("frappe.translate.get_all_translations", return_value={}))
        self.enterContext(patch.object(frappe, "throw", side_effect=_throw))
        self.profile = _profile()
        self.get_profile = self.enterContext(
            patch.object(frappe, "get_cached_doc", return_value=self.profile)
        )
        self.enabled = self.enterContext(
            patch.object(frappe, "get_cached_value", return_value=1)
        )
        frappe.db.get_value.return_value = 0

    def invoice_context(self):
        invoice = SimpleNamespace(
            doctype="POS Invoice", items=[], taxes=[], payments=[], grand_total=38,
            base_total_taxes_and_charges=3.61, rounded_total=0, name="TEST-INVOICE",
            pos_profile="TEST POS", customer="TEST CUSTOMER", is_return=0,
            account_for_change_amount="TEST ACCOUNT",
            set_warehouse=None,
            flags=frappe._dict(), save=Mock(), submit=Mock(), run_method=Mock(),
        )
        invoice.get = lambda field: getattr(invoice, field, None)
        invoice.append = lambda field, row: getattr(invoice, field).append(_Row(row))
        invoice.set = lambda field, value: setattr(invoice, field, value)
        invoice.validate = Mock()
        order = SimpleNamespace(
            company="TEST COMPANY", pos_profile="TEST POS", selling_price_list="TEST PRICE",
            customer="TEST CUSTOMER", service_type="Pickup", transfer_order_values=Mock(),
        )
        entry = frappe._dict(
            identifier="pya_test", item_code="TEST DISH", qty=1, price_list_rate=38,
            rate=38, discount_percentage=0, discount_amount=0, unit_value=0,
            item_tax_template=None, item_tax_rate="{}", has_serial_no=0, serial_no=None,
            has_batch_no=0, batch_no=None,
        )
        self.enterContext(patch.object(frappe, "new_doc", return_value=invoice))
        self.enterContext(patch.object(module, "apply_restaurant_pos_currency"))
        self.enterContext(patch.object(module, "enforce_restaurant_pos_invoice_currency"))
        return order, invoice, {entry.identifier: entry}

    def test_profile_default_not_named_cash_is_selected(self):
        self.profile.payments.insert(0, frappe._dict(mode_of_payment="Other", default=0))
        self.assertEqual(module.get_pos_preview_payment_method("TEST POS", "TEST COMPANY"), "Transferencia")
        self.enabled.assert_called_once_with("Mode of Payment", "Transferencia", "enabled")
        frappe.db.set_value.assert_not_called()

    def test_missing_or_ambiguous_default_is_rejected(self):
        cases = [[], [frappe._dict(mode_of_payment="Other", default=0)],
                 [frappe._dict(mode_of_payment=None, default=1)],
                 self.profile.payments + self.profile.payments]
        for rows in cases:
            with self.subTest(rows=rows):
                self.profile.payments = rows
                with self.assertRaisesRegex(frappe.ValidationError, "único.*TEST POS"):
                    module.get_pos_preview_payment_method("TEST POS", "TEST COMPANY")

    def test_disabled_or_missing_default_does_not_fall_back_to_another_method(self):
        self.profile.payments.append(frappe._dict(mode_of_payment="Other", default=0))
        for enabled in (0, None):
            with self.subTest(enabled=enabled):
                self.enabled.return_value = enabled
                with self.assertRaisesRegex(frappe.ValidationError, "TEST POS.*habilitado"):
                    module.get_pos_preview_payment_method("TEST POS", "TEST COMPANY")
        frappe.db.set_value.assert_not_called()

    def test_wrong_company_or_disabled_profile_is_rejected(self):
        for company, disabled in (("OTHER COMPANY", 0), ("TEST COMPANY", 1)):
            with self.subTest(company=company, disabled=disabled):
                self.profile.company, self.profile.disabled = company, disabled
                with self.assertRaisesRegex(frappe.ValidationError, "perfil POS habilitado"):
                    module.get_pos_preview_payment_method("TEST POS", "TEST COMPANY")

    def test_get_invoice_validates_configured_preview_without_persisting(self):
        order, invoice, entries = self.invoice_context()
        snapshots = []
        invoice.validate.side_effect = lambda: snapshots.append([dict(row) for row in invoice.payments])

        result = module.TableOrder.get_invoice(order, entries)

        self.assertIs(result, invoice)
        self.assertEqual(snapshots, [[{"mode_of_payment": "Transferencia", "amount": 38}]])
        self.assertEqual(invoice.items[0].rate, 38)
        self.assertEqual(invoice.grand_total, 38)
        invoice.run_method.assert_any_call("calculate_taxes_and_totals")
        invoice.validate.assert_called_once_with()
        invoice.save.assert_not_called()
        invoice.submit.assert_not_called()
        frappe.db.commit.assert_not_called()
        frappe.db.set_value.assert_not_called()

    def test_invalid_default_is_reported_before_native_set_missing_values(self):
        order, invoice, entries = self.invoice_context()
        self.enabled.return_value = 0
        with self.assertRaisesRegex(frappe.ValidationError, "TEST POS.*habilitado"):
            module.TableOrder.get_invoice(order, entries)
        invoice.run_method.assert_not_called()
        invoice.save.assert_not_called()

    def test_native_pos_fields_does_not_refresh_unrelated_profile_payments(self):
        for payments in (None, {"Tarjeta": 38}):
            with self.subTest(payments=payments):
                order, invoice, entries = self.invoice_context()
                self.profile.payments.append(frappe._dict(mode_of_payment="Disabled", default=0))
                frappe.db.get_value.side_effect = lambda doctype, *args, **kwargs: (
                    (None, None, None) if doctype == "Customer" else 0
                )
                invoice.run_method.side_effect = lambda method: (
                    POSInvoice.set_pos_fields(invoice) if method == "set_missing_values" else None
                )
                with (
                    patch.object(frappe, "get_doc", return_value=self.profile),
                    patch("erpnext.stock.get_item_details.get_pos_profile_item_details", return_value={}),
                    patch("erpnext.accounts.doctype.pos_invoice.pos_invoice.update_multi_mode_option") as refresh,
                ):
                    module.TableOrder.get_invoice(order, entries, mode_of_payment=payments)
                refresh.assert_not_called()
                self.assertEqual(invoice.payments[0].mode_of_payment, "Transferencia" if payments is None else "Tarjeta")
                self.assertEqual(invoice.payments[0].amount, 38)

    def test_explicit_mixed_payments_are_used_at_first_validation(self):
        order, invoice, entries = self.invoice_context()
        self.enabled.return_value = 0  # Must not force a disabled preview default.
        payments = {"Tarjeta": 30.25, "Efectivo": 7.75}
        snapshots = []
        invoice.validate.side_effect = lambda: snapshots.append([dict(row) for row in invoice.payments])

        module.TableOrder.get_invoice(order, entries, True, mode_of_payment=payments)

        self.assertEqual(snapshots, [[{"mode_of_payment": key, "amount": value}
                                     for key, value in payments.items()]])
        self.get_profile.assert_not_called()
        self.enabled.assert_not_called()
        self.assertEqual(payments, {"Tarjeta": 30.25, "Efectivo": 7.75})

    def test_explicit_empty_payment_never_uses_default(self):
        order, invoice, entries = self.invoice_context()
        with self.assertRaisesRegex(frappe.ValidationError, "At least one mode"):
            module.TableOrder.get_invoice(order, entries, True, mode_of_payment={})
        invoice.validate.assert_not_called()
        invoice.save.assert_not_called()
        self.get_profile.assert_not_called()

    def test_native_missing_company_account_error_is_not_suppressed(self):
        order, invoice, entries = self.invoice_context()
        frappe.db.get_value.return_value = None
        invoice.validate.side_effect = lambda: get_bank_cash_account(
            invoice.payments[0].mode_of_payment, order.company
        )
        # The native account helper formats a link through this pure URL helper.
        with patch("erpnext.accounts.doctype.sales_invoice.sales_invoice.get_link_to_form", return_value="Transferencia"):
            with self.assertRaisesRegex(frappe.ValidationError, "Please set default Cash or Bank account"):
                module.TableOrder.get_invoice(order, entries)
        invoice.save.assert_not_called()
        invoice.submit.assert_not_called()

    def test_native_invalid_explicit_payment_error_is_not_suppressed(self):
        order, invoice, entries = self.invoice_context()
        invoice.validate.side_effect = frappe.ValidationError("Mode of Payment disabled")
        with self.assertRaisesRegex(frappe.ValidationError, "Mode of Payment disabled"):
            module.TableOrder.get_invoice(order, entries, True, mode_of_payment={"Disabled": 38})
        self.assertEqual(invoice.payments[0].mode_of_payment, "Disabled")
        invoice.save.assert_not_called()

    def assert_cashier_payments(self, discount=0):
        order, invoice, entries = self.invoice_context()
        order.owner = "TEST WAITER"
        order.get = lambda field: getattr(order, field, None)
        order.link_invoice = None
        order.is_dine_in = True
        order.save, order.reload, order.submit, order.synchronize = Mock(), Mock(), Mock(), Mock()
        order.entry_items = [
            SimpleNamespace(**row, as_dict=lambda row=row: dict(row))
            for row in entries.values()
        ]
        order.discount, order.discount_global_percent = discount, 0
        order.context_label = "TEST TABLE"
        order.amount = 38
        order.get_invoice = Mock(side_effect=lambda rows, make, **kw: module.TableOrder.get_invoice(order, rows, make, **kw))
        payments = {"Tarjeta": 30.25 - discount, "Efectivo": 7.75}
        snapshots = []
        invoice.docstatus, invoice.is_return = 0, False

        def validate_payments():
            invoice.grand_total = 38 - getattr(invoice, "discount_amount", 0)
            invoice.paid_amount = sum(row.amount for row in invoice.payments)
            POSInvoice.validate_payment_amount(invoice)
            POSInvoice.validate_full_payment(invoice)
            snapshots.append([dict(row) for row in invoice.payments])

        def submit():
            invoice.docstatus = 1
            validate_payments()

        invoice.validate.side_effect = validate_payments
        invoice.submit.side_effect = submit
        with (
            patch.object(module, "get_restaurant_payment_permissions", return_value=frappe._dict(can_pay=True, has_direct_invoice_permission=True)),
            patch.object(module, "validate_tip_request", return_value=None),
            patch.object(module, "create_tip_record", return_value=None),
            patch.object(module, "get_customer_identity", return_value=frappe._dict(tipo_documento_identidad="DNI", tax_id="00000000")),
            patch.object(module, "get_restaurant_settings", return_value=frappe._dict(serie_boleta_m="TEST-.#####")),
            patch.object(frappe, "msgprint"),
        ):
            result = module.TableOrder.make_invoice(
                order, payments, customer="TEST CUSTOMER", guest_count=1,
                voucher_type="Boleta", emission_mode="Manual",
            )
        expected = [{"mode_of_payment": key, "amount": value} for key, value in payments.items()]
        self.assertEqual(snapshots, [expected, expected, expected])
        order.get_invoice.assert_called_once_with(entries, True, mode_of_payment=payments)
        self.assertEqual(result["invoice_name"], "TEST-INVOICE")
        invoice.save.assert_called_once_with()
        invoice.submit.assert_called_once_with()

    def test_make_invoice_preserves_mixed_payments_through_submission(self):
        self.assert_cashier_payments()

    def test_make_invoice_preserves_discounted_mixed_payments(self):
        self.assert_cashier_payments(discount=8)

    def test_pedidosya_import_reaches_real_item_and_aggregate_invoice_builders(self):
        order, invoice, _ = self.invoice_context()
        order.name, order.context_label = "TEST-ORDER", "Pickup"
        order.entry_items = []
        order.insert, order.save, order.reload, order.validate = Mock(), Mock(), Mock(), Mock()
        order._validate_delivery_fee_item_change = Mock()
        order.get_invoice = MethodType(module.TableOrder.get_invoice, order)
        order.update_item = MethodType(module.TableOrder.update_item, order)
        order.aggregate = MethodType(module.TableOrder.aggregate, order)
        order.append = lambda field, row: getattr(order, field).append(
            SimpleNamespace(**row, as_dict=lambda: dict(row))
        )
        self.profile.taxes_and_charges, self.profile.selling_price_list = "TEST TAX", "TEST PRICE"
        item = frappe._dict(name="TEST DISH", disabled=0, is_sales_item=1, has_batch_no=0, has_serial_no=0)
        self.get_profile.side_effect = lambda doctype, name: self.profile if doctype == "POS Profile" else item
        frappe.db.count.return_value, frappe.db.sql.return_value = 0, []

        def fill_items(method):
            if method == "set_missing_values":
                for row in invoice.items:
                    row.item_group, row.discount_amount = "TEST GROUP", 0

        invoice.run_method.side_effect = fill_items
        fulfillment = SimpleNamespace(insert=Mock())
        settings = frappe._dict(
            company=order.company, pos_profile=order.pos_profile, default_customer=order.customer,
            amount_tolerance=0.01, fallback_contact_phone="000000000",
            default_payment_timing="Prepaid", expected_payment_method=None,
        )
        inbox = SimpleNamespace(
            expedition_type="Pickup", external_total=38, delivery_provider="Customer Pickup",
            external_code="TEST-EXTERNAL", middleware_token="TEST-TOKEN",
        )
        lines = [{"item_code": "TEST DISH", "qty": 1, "rate": 38, "notes": "TEST ONLY"}]
        with (
            patch.object(frappe, "get_doc", side_effect=[order, fulfillment]),
            patch.object(frappe, "generate_hash", return_value="testhash"),
        ):
            imported_order, imported_fulfillment = service._create_restaurant_documents(inbox, settings, {}, lines)

        self.assertIs(imported_order, order)
        self.assertIs(imported_fulfillment, fulfillment)
        self.assertEqual(order.amount, 38)
        self.assertEqual(order.entry_items[0].rate, 38)
        self.assertEqual(invoice.validate.call_count, 2)  # update_item and aggregate
        self.assertEqual(invoice.payments[0].mode_of_payment, "Transferencia")
        fulfillment.insert.assert_called_once_with()
        invoice.save.assert_not_called()
        invoice.submit.assert_not_called()
        frappe.db.commit.assert_not_called()

    def test_make_invoice_missing_payment_is_rejected_before_saving_order(self):
        order, invoice, _ = self.invoice_context()
        order.get = lambda field: None
        order.owner = "TEST WAITER"
        order.save = Mock()
        with patch.object(module, "get_restaurant_payment_permissions", return_value=frappe._dict(can_pay=True)):
            for payments in (None, {}):
                with self.subTest(payments=payments), self.assertRaisesRegex(frappe.ValidationError, "At least one mode"):
                    module.TableOrder.make_invoice(order, payments)
        order.save.assert_not_called()
        invoice.save.assert_not_called()
