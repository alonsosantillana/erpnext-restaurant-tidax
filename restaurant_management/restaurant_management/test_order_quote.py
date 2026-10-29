"""Offline R9E.2 contracts, not a live site or localization certification.

Use python -B -m unittest, never bench run-tests on an operational site.
The real POSInvoice constructor, price helper and tax engine run with synthetic
read/metadata fixtures; regional round-off dispatch is explicitly out of scope.
"""

import copy
import importlib
import json
import socket
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import frappe
import erpnext
from frappe.model.document import Document
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
from erpnext.stock import get_item_details as native_prices

from restaurant_management.restaurant_management import order_quote as quote


native_tax = importlib.import_module("erpnext.controllers.taxes_and_totals")


class ReadDocument(frappe._dict):
    def check_permission(self, permission):
        if self.get("denied"):
            raise frappe.PermissionError("Synthetic denied document")


class Metadata:
    """Unmodified native JSON fields, with explicit synthetic numeric precision."""

    def __init__(self, doctype):
        slug = frappe.scrub(doctype)
        path = Path(erpnext.__file__).parent / "accounts" / "doctype" / slug / (slug + ".json")
        data = json.loads(path.read_text())
        self.fields = [frappe._dict(row) for row in data["fields"]]
        for field in self.fields:
            if field.fieldtype in {"Currency", "Float", "Percent"}:
                field.precision = 2 if field.fieldtype == "Currency" else 6
        self.columns = [row.fieldname for row in self.fields]

    def get_table_fields(self):
        return [row for row in self.fields if row.fieldtype == "Table"]

    def get_field(self, name):
        return next((row for row in self.fields if row.fieldname == name), None)

    def get_label(self, name):
        return name

    def get(self, key, filters=None):
        if key != "fields":
            return None
        if filters:
            return [row for row in self.fields if row.fieldtype in {"Currency", "Float", "Percent"}]
        return self.fields


class TestReadonlyOrderQuote(unittest.TestCase):
    def setUp(self):
        storage = frappe.local._Local__storage
        previous = storage.get({})
        storage.set({})
        self.addCleanup(storage.set, previous)
        self.guard_calls = []

        def denied(*args, **kwargs):
            self.guard_calls.append("side effect")
            raise AssertionError("No site, DB mutation, POS validation or network")

        for name in ("init", "connect", "new_doc", "set_user"):
            self.enterContext(patch.object(frappe, name, side_effect=denied))
        for name in ("save", "insert", "submit", "db_set", "run_method"):
            self.enterContext(patch.object(Document, name, side_effect=denied))
        for name in ("validate", "set_missing_values"):
            self.enterContext(patch.object(POSInvoice, name, side_effect=denied))
        for name in ("create_connection", "getaddrinfo"):
            self.enterContext(patch.object(socket, name, side_effect=denied))
        self.enterContext(patch.object(socket.socket, "connect", side_effect=denied))
        self.enterContext(patch.object(native_prices, "insert_item_price", side_effect=denied))
        self.enterContext(patch("erpnext.setup.utils.get_exchange_rate", side_effect=denied))
        self.enterContext(patch("frappe.translate.get_all_translations", return_value={}))
        self.enterContext(patch.object(frappe, "get_system_settings", return_value="Banker's Rounding"))
        self.enterContext(patch.object(frappe, "get_hooks", return_value={}))
        self.enterContext(patch.object(frappe, "render_template", return_value="<synthetic-html>"))
        self.round_row_wise = 0
        self.disable_rounding = 1
        frappe.local.db = SimpleNamespace(
            get_value=self.db_value, exists=self.exists,
            get_single_value=self.single_value,
            set_value=denied, insert=denied, commit=denied, rollback=denied,
            sql=denied, delete=denied, truncate=denied,
        )
        frappe.local.flags = frappe._dict()
        frappe.local.session = frappe._dict(user="api-test")
        frappe.local.valid_columns = {}
        self.meta = {}
        self.enterContext(patch.object(frappe, "get_meta", side_effect=self.get_meta))
        self.enterContext(patch("frappe.model.base_document.get_controller", return_value=Document))
        self.enterContext(patch.object(frappe, "get_doc", side_effect=self.get_doc))
        self.enterContext(patch.object(frappe, "get_cached_doc", side_effect=self.get_doc))
        self.enterContext(patch.object(frappe, "get_cached_value", side_effect=self.cached_value))
        self.enterContext(patch.object(frappe, "get_all", side_effect=self.get_all))
        self.enterContext(patch.object(frappe, "has_permission", return_value=True))
        self.enterContext(patch.object(native_prices, "get_item_price", side_effect=self.price_rows))
        self.enterContext(patch.object(quote, "today", return_value="2030-01-01"))
        self.docs, self.rules = {}, set()
        self.doc("Company", "CO", default_currency="PEN")
        self.doc("Currency", "PEN", smallest_currency_fraction_value=1)
        self.doc("User", "api-test", enabled=1, user_type="System User")
        self.doc("POS Profile", "POS", company="CO", currency="PEN", disabled=0,
                 selling_price_list="LIST", taxes_and_charges="TAXES",
                 posa_tax_inclusive=0, disable_rounded_total=1)
        self.doc("Price List", "LIST", enabled=1, selling=1, currency="PEN")
        self.doc("Restaurant Company Settings", "SETTINGS", company="CO", pos_profile="POS",
                 enable_pickup=1, enable_delivery=1, delivery_fee_item="FEE")
        self.doc("Customer", "CUSTOMER", disabled=0, customer_group="GROUP")
        self.doc("Address", "ADDRESS", links=[frappe._dict(link_doctype="Customer", link_name="CUSTOMER")])
        self.doc("Account", "VAT", company="CO", account_type="Tax", is_group=0, disabled=0)
        self.doc("Sales Taxes and Charges Template", "TAXES", company="CO", disabled=0,
                 taxes=[frappe._dict(charge_type="On Net Total", account_head="VAT", rate=18)])
        self.doc("Item Group", "FOOD", parent_item_group=None, taxes=[])
        for code, price in (("DISH", 100), ("DRINK", 50), ("FEE", 10)):
            self.doc("Item", code, is_sales_item=1, is_stock_item=0, stock_uom="Unit", item_group="FOOD")
            self.doc("Item Price", "PRICE-" + code, item_code=code, price_list="LIST",
                     uom="Unit", selling=1, buying=0, currency="PEN", price_list_rate=price)
        self.context = dict(company="CO", pos_profile="POS", selling_price_list="LIST",
                            profile_modified="2030-01-01 00:00:00", currency="PEN")
        self.proposal = dict(service_type="Pickup", customer="CUSTOMER", phone="+51999999999",
                             promised_at=(datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
                             items=[dict(item_code="DISH", qty=2, note=""),
                                    dict(item_code="DRINK", qty=1, note="No sugar")])

    def tearDown(self):
        self.assertEqual(self.guard_calls, [])

    def doc(self, doctype, name, **values):
        result = ReadDocument(doctype=doctype, name=name, modified="2030-01-01 00:00:00", **values)
        self.docs[doctype, name] = result
        return result

    def get_doc(self, doctype, name):
        return self.docs[doctype, name]

    def get_meta(self, doctype):
        if doctype not in self.meta:
            self.meta[doctype] = Metadata(doctype)
            frappe.local.valid_columns[doctype] = self.meta[doctype].columns
        return self.meta[doctype]

    def db_value(self, doctype, name, fields, as_dict=False, **kwargs):
        if doctype == "DefaultValue":
            return "CO"
        if doctype == "Restaurant Company Settings":
            return "SETTINGS"
        document = self.get_doc(doctype, name)
        if isinstance(fields, list):
            return frappe._dict({field: document.get(field) for field in fields})
        return document.get(fields)

    def cached_value(self, doctype, name, field, **kwargs):
        return self.db_value(doctype, name, field, **kwargs)

    def exists(self, doctype, filters):
        return doctype in self.rules

    def single_value(self, doctype, field):
        if (doctype, field) == ("Accounts Settings", "round_row_wise_tax"):
            return self.round_row_wise
        if (doctype, field) == ("Global Defaults", "disable_rounded_total"):
            return self.disable_rounding
        raise AssertionError((doctype, field))

    def get_all(self, doctype, filters, **kwargs):
        self.assertEqual(doctype, "Item Price")
        return [frappe._dict(name=d.name) for (dt, _), d in self.docs.items()
                if dt == doctype and all(d.get(k) == v for k, v in filters.items())]

    def price_rows(self, args, item_code, ignore_party=False, **kwargs):
        # Synthetic database selection only; price conversion/packing and all tax
        # arithmetic are the actual unmodified native helper/engine.
        rows = []
        for (dt, _), d in self.docs.items():
            if dt != "Item Price" or d.item_code != item_code or d.price_list != args["price_list"]:
                continue
            if d.get("customer") != args.get("customer"):
                continue
            rows.append((d.name, d.price_list_rate, d.uom))
        return rows

    def run_quote(self):
        return quote.quote_order(copy.deepcopy(self.proposal), dict(self.context))

    def test_exclusive_whole_cart_uses_real_native_engine(self):
        with patch.object(quote, "calculate_taxes_and_totals", wraps=native_tax.calculate_taxes_and_totals) as engine:
            result = self.run_quote()
        self.assertEqual(engine.call_count, 1)
        self.assertIsInstance(engine.call_args.args[0], POSInvoice)
        self.assertEqual(result["total"], "295")
        self.assertEqual(result["tax"], "45")
        self.assertEqual(result["delivery_fee"], "0")
        self.assertEqual(result["lines"], [dict(item_code="DISH", qty=2, rate="100", amount="200"),
                                            dict(item_code="DRINK", qty=1, rate="50", amount="50")])
        self.assertEqual(set(result), {"currency", "lines", "tax", "total", "delivery_fee", "native_fingerprint"})
        self.assertRegex(result["native_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertTrue(all(type(row["qty"]) is int for row in result["lines"]))

    def test_total_beyond_tix_nine_integer_digits_is_handoff(self):
        self.proposal["items"] = [dict(item_code="DISH", qty=1000, note="")]
        self.docs["Item Price", "PRICE-DISH"].price_list_rate = 800000
        self.docs["Sales Taxes and Charges Template", "TAXES"].taxes[0].rate = 25
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_inclusive_tax_is_native_and_not_added_twice(self):
        self.docs["POS Profile", "POS"].posa_tax_inclusive = 1
        result = self.run_quote()
        self.assertEqual(result["total"], "250")
        self.assertEqual(result["tax"], "38.13")
        self.assertEqual([row["amount"] for row in result["lines"]], ["200", "50"])

    def test_delivery_fee_once_exclusive_and_inclusive(self):
        self.proposal.update(service_type="Delivery", address="ADDRESS")
        for inclusive, total, tax in ((0, "306.8", "46.8"), (1, "260", "39.66")):
            with self.subTest(inclusive=inclusive):
                self.docs["POS Profile", "POS"].posa_tax_inclusive = inclusive
                result = self.run_quote()
                self.assertEqual(result["total"], total)
                self.assertEqual(result["tax"], tax)
                self.assertEqual(result["delivery_fee"], "10")
                self.assertEqual(len(result["lines"]), 2)

    def add_service_charge(self, rate=13, root_type="Expense", account_type=""):
        self.doc("Account", "SERVICE", company="CO", account_type=account_type,
                 root_type=root_type, report_type="Profit and Loss", is_group=0, disabled=0)
        self.docs["Sales Taxes and Charges Template", "TAXES"].taxes.append(
            frappe._dict(charge_type="On Net Total", account_head="SERVICE", rate=rate))

    def test_configured_charges_service_and_inclusion_matrix(self):
        self.docs["Sales Taxes and Charges Template", "TAXES"].taxes[0].rate = 10.5
        self.docs["Item Price", "PRICE-FEE"].price_list_rate = 6.5
        tax_only = copy.deepcopy(self.docs)
        for charge in (False, True):
            for delivery in (False, True):
                for inclusive in (0, 1):
                    with self.subTest(charge=charge, delivery=delivery, inclusive=inclusive):
                        self.docs = copy.deepcopy(tax_only)
                        if charge:
                            self.add_service_charge()
                        self.docs["POS Profile", "POS"].posa_tax_inclusive = inclusive
                        self.proposal["service_type"] = "Delivery" if delivery else "Pickup"
                        if delivery:
                            self.proposal["address"] = "ADDRESS"
                        else:
                            self.proposal.pop("address", None)
                        before = copy.deepcopy(self.docs)
                        with patch.object(quote, "calculate_taxes_and_totals", wraps=native_tax.calculate_taxes_and_totals) as engine:
                            result = self.run_quote()
                        self.assertEqual(engine.call_count, 1)
                        invoice = engine.call_args.args[0]
                        self.assertEqual(len(invoice.items), 3 if delivery else 2)
                        self.assertEqual(sum(row.item_code == "FEE" for row in invoice.items), int(delivery))
                        self.assertEqual([row.account_head for row in invoice.taxes],
                                         ["VAT", "SERVICE"] if charge else ["VAT"])
                        self.assertEqual([row.rate for row in invoice.taxes],
                                         [10.5, 13] if charge else [10.5])
                        self.assertTrue(all(row.included_in_print_rate == inclusive for row in invoice.taxes))
                        expected = (("316.77" if delivery else "308.75") if charge
                                    else ("283.43" if delivery else "276.25"))
                        self.assertEqual(result["total"], ("256.5" if delivery else "250") if inclusive else expected)
                        if not inclusive:
                            self.assertEqual(result["tax"], (("60.27" if delivery else "58.75") if charge
                                             else ("26.93" if delivery else "26.25")))
                            if charge:
                                self.assertEqual([row.tax_amount for row in invoice.taxes],
                                                 [26.93, 33.34] if delivery else [26.25, 32.5])
                        self.assertGreater(float(result["tax"]), 0)
                        self.assertEqual(result["delivery_fee"], "6.5" if delivery else "0")
                        self.assertEqual(len(result["lines"]), 2)
                        self.assertEqual(self.docs, before)

    def test_charge_percentage_and_income_expense_types_are_configurable(self):
        self.proposal["items"] = [dict(item_code="DISH", qty=1)]
        self.docs["Sales Taxes and Charges Template", "TAXES"].taxes[0].rate = 10.5
        self.add_service_charge(rate=7.25)
        account = self.docs["Account", "SERVICE"]
        for root, types in (
            ("Income", (None, "", "Chargeable", "Income Account", "Direct Income", "Indirect Income")),
            ("Expense", (None, "", "Chargeable", "Expense Account", "Direct Expense", "Indirect Expense")),
        ):
            for account_type in types:
                with self.subTest(root=root, account_type=account_type):
                    account.update(root_type=root, account_type=account_type)
                    self.assertEqual(self.run_quote()["total"], "117.75")

    def test_charge_account_scope_and_classification_fail_closed(self):
        self.add_service_charge()
        account = self.docs["Account", "SERVICE"]
        original = dict(account)
        for mutation in (dict(company="OTHER"), dict(disabled=1), dict(is_group=1),
                         dict(denied=True), dict(root_type="Liability"), dict(root_type="Asset"),
                         dict(root_type="Equity"), dict(root_type=None), dict(report_type=None),
                         dict(report_type="Balance Sheet"), dict(account_type="Bank"),
                         dict(account_type="Cash"), dict(account_type="Receivable"),
                         dict(account_type="Payable"), dict(account_type="Stock"),
                         dict(account_type="Round Off"), dict(account_type="Unsupported")):
            with self.subTest(mutation=mutation):
                account.update(mutation)
                with self.assertRaises(quote.QuoteUnavailable):
                    self.run_quote()
                account.clear()
                account.update(original)

    def test_service_charge_rows_keep_existing_support_limits(self):
        self.add_service_charge()
        template = self.docs["Sales Taxes and Charges Template", "TAXES"]
        row = template.taxes[-1]
        original = dict(row)
        for mutation in (dict(rate=-1), dict(rate=101), dict(rate="NaN"),
                         dict(add_deduct_tax="Deduct"), dict(dont_recompute_tax=1),
                         dict(charge_type="On Previous Row Total")):
            with self.subTest(mutation=mutation):
                row.update(mutation)
                with self.assertRaises(quote.QuoteUnavailable):
                    self.run_quote()
                row.clear()
                row.update(original)
        template.taxes.append(copy.deepcopy(row))
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_charge_eligibility_and_rate_are_fingerprinted(self):
        self.add_service_charge()
        first = self.run_quote()
        self.docs["Account", "SERVICE"].root_type = "Income"
        second = self.run_quote()
        self.assertEqual(first["total"], second["total"])
        self.assertNotEqual(first["native_fingerprint"], second["native_fingerprint"])
        self.docs["Account", "SERVICE"].account_type = "Chargeable"
        third = self.run_quote()
        self.assertNotEqual(second["native_fingerprint"], third["native_fingerprint"])
        self.docs["Sales Taxes and Charges Template", "TAXES"].taxes[-1].rate = 7.25
        fourth = self.run_quote()
        self.assertNotEqual(third["total"], fourth["total"])
        self.assertNotEqual(third["native_fingerprint"], fourth["native_fingerprint"])

    def test_fractional_multi_item_native_rounding(self):
        self.docs["Item Price", "PRICE-DISH"].price_list_rate = 0.99
        self.docs["Item Price", "PRICE-DRINK"].price_list_rate = 0.33
        result = self.run_quote()
        self.assertEqual(result["total"], "2.73")
        self.assertEqual(result["tax"], "0.42")

    def test_snapshot_is_deterministic_and_input_not_mutated(self):
        proposal, context = copy.deepcopy(self.proposal), dict(self.context)
        first, second = self.run_quote(), self.run_quote()
        self.assertEqual(first, second)
        self.assertEqual(self.proposal, proposal)
        self.assertEqual(self.context, context)
        self.docs["Item Price", "PRICE-DISH"].price_list_rate = 101
        self.assertNotEqual(self.run_quote()["native_fingerprint"], first["native_fingerprint"])

    def test_human_revalidation_uses_bound_pos_not_default_and_same_fingerprint(self):
        first = self.run_quote()
        self.doc("User", "human-test", enabled=1, user_type="System User")
        frappe.session.user = "human-test"
        self.assertEqual(self.run_quote(), first)

    def test_stale_or_foreign_context_rejected(self):
        for field, value in (("company", "FOREIGN"), ("profile_modified", "old"),
                             ("selling_price_list", "FOREIGN"), ("currency", "USD")):
            with self.subTest(field=field):
                context = {**self.context, field: value}
                with self.assertRaises((quote.QuoteUnavailable, KeyError)):
                    quote.quote_order(self.proposal, context)

    def test_disabled_guest_or_non_system_actor_rejected(self):
        for user, enabled, user_type in (("Guest", 1, "System User"), ("api-test", 0, "System User"),
                                          ("api-test", 1, "Website User")):
            with self.subTest(user=user, enabled=enabled, user_type=user_type):
                frappe.session.user = user
                self.docs["User", "api-test"].update(enabled=enabled, user_type=user_type)
                with self.assertRaises(quote.QuoteUnavailable):
                    self.run_quote()

    def test_bound_profile_permission_and_applicability_rejected(self):
        profile = self.docs["POS Profile", "POS"]
        profile.denied = True
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()
        profile.denied = False
        profile.applicable_for_users = [frappe._dict(user="another-user")]
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_disabled_service_or_customer_rejected(self):
        self.docs["Restaurant Company Settings", "SETTINGS"].enable_pickup = 0
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()
        self.docs["Restaurant Company Settings", "SETTINGS"].enable_pickup = 1
        self.docs["Customer", "CUSTOMER"].disabled = 1
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_foreign_address_and_pickup_address_rejected(self):
        self.proposal["address"] = "ADDRESS"
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()
        self.proposal["service_type"] = "Delivery"
        self.docs["Address", "ADDRESS"].links[0].link_name = "OTHER"
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_rules_and_tax_categories_rejected(self):
        for rule in ("Pricing Rule", "Tax Rule"):
            self.rules = {rule}
            with self.subTest(rule=rule), self.assertRaises(quote.QuoteUnavailable):
                self.run_quote()
        self.rules = set()
        self.docs["Customer", "CUSTOMER"].tax_category = "SPECIAL"
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_item_tax_and_ancestor_group_tax_rejected(self):
        self.docs["Item", "DISH"].taxes = [frappe._dict(item_tax_template="SPECIAL")]
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()
        self.docs["Item", "DISH"].taxes = []
        self.docs["Item Group", "FOOD"].parent_item_group = "PARENT"
        self.doc("Item Group", "PARENT", taxes=[frappe._dict(item_tax_template="SPECIAL")])
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_missing_ambiguous_zero_expired_and_mismatched_price_rejected(self):
        price = self.docs["Item Price", "PRICE-DISH"]
        for mutation in (dict(price_list_rate=0), dict(currency="USD"), dict(uom="Box"),
                         dict(valid_upto="2029-12-31"), dict(valid_from="2030-01-02"),
                         dict(price_list_rate=float("nan")), dict(price_list_rate="1.1234567")):
            original = dict(price)
            with self.subTest(mutation=mutation):
                price.update(mutation)
                with self.assertRaises(quote.QuoteUnavailable):
                    self.run_quote()
            price.clear()
            price.update(original)
        self.docs.pop(("Item Price", "PRICE-DISH"))
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()
        self.docs["Item Price", "PRICE-DISH"] = price
        self.docs["Item Price", "DUPLICATE"] = ReadDocument({**price, "name": "DUPLICATE"})
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_item_price_permission_and_packing_rejected(self):
        with patch.object(frappe, "has_permission", return_value=False):
            with self.assertRaises(quote.QuoteUnavailable):
                self.run_quote()
        self.docs["Item Price", "PRICE-DISH"].packing_unit = 3
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_fee_cannot_be_supplied_as_product_or_stock_item(self):
        self.proposal["items"][0]["item_code"] = "FEE"
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()
        self.proposal["items"][0]["item_code"] = "DISH"
        self.proposal.update(service_type="Delivery", address="ADDRESS")
        self.docs["Item", "FEE"].is_stock_item = 1
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_unsupported_tax_rows_and_account_rejected(self):
        template = self.docs["Sales Taxes and Charges Template", "TAXES"]
        template.taxes[0].charge_type = "Actual"
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()
        template.taxes[0].charge_type = "On Net Total"
        self.docs["Account", "VAT"].company = "OTHER"
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_untrusted_amount_fields_and_cart_bounds_rejected(self):
        for mutation in (dict(rate=1), dict(items=[]),
                         dict(items=[dict(item_code="DISH", qty=True)]),
                         dict(items=[dict(item_code="DISH", qty=1001)]),
                         dict(items=[dict(item_code="DISH", qty=1, rate=1)]),
                         dict(items=self.proposal["items"] * 2)):
            with self.subTest(mutation=mutation), self.assertRaises(quote.QuoteUnavailable):
                quote.quote_order({**self.proposal, **mutation}, self.context)

    def test_item_eligibility_flags_and_group_cycle_rejected(self):
        item = self.docs["Item", "DISH"]
        for field in ("disabled", "has_serial_no", "has_batch_no", "has_variants",
                      "variant_of", "is_fixed_asset", "is_customer_provided_item"):
            with self.subTest(field=field):
                item[field] = 1
                with self.assertRaises(quote.QuoteUnavailable):
                    self.run_quote()
                item.pop(field)
        self.docs["Item Group", "FOOD"].parent_item_group = "FOOD"
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_native_region_override_and_empty_tax_template_rejected(self):
        self.docs["Company", "CO"].country = "COUNTRY"
        hooks = {"COUNTRY": {"erpnext.controllers.taxes_and_totals.update_itemised_tax_data": ["custom.override"]}}
        with patch.object(frappe, "get_hooks", return_value=hooks):
            with self.assertRaises(quote.QuoteUnavailable):
                self.run_quote()
        self.docs["Sales Taxes and Charges Template", "TAXES"].taxes = []
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_native_rounding_adjustment_rejected_not_silently_ignored(self):
        self.disable_rounding = 0
        self.docs["Item Price", "PRICE-DISH"].price_list_rate = 0.99
        self.docs["Item Price", "PRICE-DRINK"].price_list_rate = 0.33
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_native_selected_price_must_equal_checked_rate(self):
        with patch.object(native_prices, "get_item_price", return_value=[("PRICE-DISH", 1, "Unit")]):
            with self.assertRaises(quote.QuoteUnavailable):
                self.run_quote()

    def test_tax_evidence_changes_fingerprint_and_money_is_bounded_string(self):
        first = self.run_quote()
        self.docs["Sales Taxes and Charges Template", "TAXES"].taxes[0].rate = 10
        second = self.run_quote()
        self.assertNotEqual(first["native_fingerprint"], second["native_fingerprint"])
        self.assertEqual(second["total"], "275")
        for key in ("tax", "total", "delivery_fee"):
            self.assertRegex(second[key], r"^[0-9]+(?:\.[0-9]{1,6})?$")

    def test_phone_promised_time_notes_and_currency_mismatch_rejected(self):
        for mutation in (dict(phone="not-a-phone"), dict(promised_at="2000-01-01T00:00:00+00:00"),
                         dict(promised_at="2030-01-01T00:00:00"),
                         dict(items=[dict(item_code="DISH", qty=1, note="x" * 501)]),
                         dict(items=[dict(item_code="DISH", qty=1, notes="old-key")])):
            with self.subTest(mutation=mutation), self.assertRaises(quote.QuoteUnavailable):
                quote.quote_order({**self.proposal, **mutation}, self.context)
        self.docs["Company", "CO"].default_currency = "USD"
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_flags_restored_after_success_and_engine_failure(self):
        frappe.flags.round_off_applicable_accounts = ["sentinel"]
        frappe.flags.round_row_wise_tax = "sentinel"
        self.run_quote()
        self.assertEqual(frappe.flags.round_off_applicable_accounts, ["sentinel"])
        self.assertEqual(frappe.flags.round_row_wise_tax, "sentinel")
        with patch.object(quote, "calculate_taxes_and_totals", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaises(RuntimeError):
                self.run_quote()
        self.assertEqual(frappe.flags.round_row_wise_tax, "sentinel")
        frappe.flags.clear()
        self.run_quote()
        self.assertNotIn("round_row_wise_tax", frappe.flags)
        self.assertNotIn("round_off_applicable_accounts", frappe.flags)


if __name__ == "__main__":
    unittest.main()
