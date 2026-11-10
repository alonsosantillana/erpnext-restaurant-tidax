"""Offline cart contracts; never initialize a site or run with bench run-tests.

Native calculation tests compose the existing guarded order fixtures. Input and
projection tests run independently of their native metadata/version requirements.
"""

import copy
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from restaurant_management.restaurant_management import order_quote as quote
from restaurant_management.restaurant_management import test_order_quote as order_fixtures


class TestCartQuoteInputs(unittest.TestCase):
    def setUp(self):
        self.context = dict(company="CO", pos_profile="POS", selling_price_list="LIST",
                            profile_modified="2030-01-01 00:00:00", currency="PEN")
        self.cart = dict(service_type="Pickup", customer="CUSTOMER",
                         items=[dict(item_code="DISH", qty=2)])
        self.proposal = {
            **copy.deepcopy(self.cart), "phone": "+51999999999",
            "promised_at": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        }
        self.enterContext(patch.object(quote, "_quote", side_effect=AssertionError("Invalid input reached pricing")))

    def reject(self, cart, context=None):
        with self.assertRaises(quote.QuoteUnavailable):
            quote.quote_cart(cart, self.context if context is None else context)

    def test_price_only_pickup_and_delivery_inputs(self):
        quote._inputs(self.cart, self.context, cart=True)
        quote._inputs({**self.cart, "service_type": "Delivery", "address": "ADDRESS"},
                      self.context, cart=True)

    def test_cart_requires_exact_dictionary_and_required_keys(self):
        for cart in (None, [], "cart", {}, frappe._dict(self.cart)):
            with self.subTest(cart=cart):
                self.reject(cart)
        for field in self.cart:
            with self.subTest(missing=field):
                self.reject({key: value for key, value in self.cart.items() if key != field})

    def test_contact_notes_and_caller_pricing_keys_are_rejected(self):
        for key in ("phone", "promised_at", "note", "notes", "rate", "total", "tax",
                    "currency", "discount_amount", "taxes_and_charges", "native_fingerprint"):
            with self.subTest(key=key):
                self.reject({**self.cart, key: "untrusted"})

    def test_context_shape_and_references_remain_strict(self):
        for context in ([], {}, frappe._dict(self.context), {**self.context, "user": "another-user"}):
            with self.subTest(context=context):
                with self.assertRaises(quote.QuoteUnavailable):
                    quote.quote_cart(self.cart, context)
        for field in self.context:
            with self.subTest(field=field):
                self.reject(self.cart, {key: value for key, value in self.context.items() if key != field})
                self.reject(self.cart, {**self.context, field: " invalid "})

    def test_pickup_forbids_even_empty_address(self):
        for value in ("ADDRESS", "", None, False, 0, [], {}):
            with self.subTest(address=value):
                self.reject({**self.cart, "address": value})

    def test_delivery_requires_address_reference(self):
        delivery = {**self.cart, "service_type": "Delivery"}
        self.reject(delivery)
        for value in ("", None, False, [], " ADDRESS", "ADDRESS\n", "x" * 141):
            with self.subTest(address=value):
                self.reject({**delivery, "address": value})

    def test_service_customer_and_item_references_are_strict(self):
        for value in (None, False, [], "Dine In", "pickup", "Delivery "):
            with self.subTest(service=value):
                self.reject({**self.cart, "service_type": value})
        for value in (None, False, [], "", " CUSTOMER", "CUSTOMER\n", "x" * 141):
            with self.subTest(reference=value):
                self.reject({**self.cart, "customer": value})
                self.reject({**self.cart, "items": [dict(item_code=value, qty=1)]})

    def test_rows_accept_only_item_code_and_qty(self):
        for row in (None, [], "DISH", {}, dict(item_code="DISH"), dict(qty=1),
                    frappe._dict(item_code="DISH", qty=1)):
            with self.subTest(row=row):
                self.reject({**self.cart, "items": [row]})
        for key in ("note", "notes", "rate", "amount", "discount_percentage", "uom", "tax"):
            with self.subTest(key=key):
                self.reject({**self.cart, "items": [dict(item_code="DISH", qty=1, **{key: ""})]})

    def test_qty_requires_exact_bounded_integer(self):
        for qty in (True, False, 0, -1, 1001, 1.0, "1", None, [], float("nan"), float("inf")):
            with self.subTest(qty=qty):
                self.reject({**self.cart, "items": [dict(item_code="DISH", qty=qty)]})
        for qty in (1, 1000):
            quote._inputs({**self.cart, "items": [dict(item_code="DISH", qty=qty)]},
                          self.context, cart=True)

    def test_item_count_and_duplicates(self):
        for rows in (None, {}, (), [], self.cart["items"] * 2,
                     [dict(item_code="ITEM-" + str(index), qty=1) for index in range(51)]):
            with self.subTest(rows=rows):
                self.reject({**self.cart, "items": rows})
        rows = [dict(item_code="ITEM-" + str(index), qty=1000) for index in range(50)]
        quote._inputs({**self.cart, "items": rows}, self.context, cart=True)

    def test_full_order_still_requires_contact_future_time_and_valid_notes(self):
        for proposal in (self.cart, {**self.proposal, "phone": "invalid"},
                         {**self.proposal, "promised_at": "2000-01-01T00:00:00+00:00"},
                         {**self.proposal, "promised_at": "2099-01-01T00:00:00"},
                         {**self.proposal, "items": [dict(item_code="DISH", qty=1, note="x" * 501)]}):
            with self.subTest(proposal=proposal), self.assertRaises(quote.QuoteUnavailable):
                quote.quote_order(proposal, self.context)
        quote._inputs({**self.proposal, "items": [dict(item_code="DISH", qty=1, note="No sugar")]},
                      self.context)
        for address in (None, "", False):
            quote._inputs({**self.proposal, "address": address}, self.context)

    def test_full_order_returns_legacy_result_and_fingerprint_unmodified(self):
        legacy = dict(currency="PEN", lines=[], tax="18", total="118", delivery_fee="0",
                      native_fingerprint="unchanged")
        with patch.object(quote, "_quote", return_value=(legacy, object())) as shared:
            result = quote.quote_order(self.proposal, self.context)
        self.assertIs(result, legacy)
        shared.assert_called_once_with(self.proposal, self.context)

    def test_cart_projects_only_financial_fields_from_native_invoice(self):
        legacy = dict(currency="PEN", lines=[dict(item_code="DISH", qty=2, rate="100", amount="200")],
                      tax="36", total="236", delivery_fee="0", native_fingerprint="private")
        invoice = SimpleNamespace(net_total=200, taxes=[
            frappe._dict(rate=18, tax_amount=36, included_in_print_rate=0,
                         account_head="PRIVATE ACCOUNT", description="PRIVATE DESCRIPTION")])
        before = copy.deepcopy(legacy)
        with patch.object(quote, "_quote", return_value=(legacy, invoice)) as shared:
            result = quote.quote_cart(self.cart, self.context)
        shared.assert_called_once_with(self.cart, self.context)
        self.assertEqual(result, {**{key: value for key, value in legacy.items() if key != "native_fingerprint"},
                                 "net_total": "200", "taxes_and_charges": [
                                     dict(ordinal=1, rate="18", tax_amount="36", included_in_print_rate=0)]})
        self.assertEqual(legacy, before)


class TestReadonlyCartQuote(unittest.TestCase):
    def setUp(self):
        self.fixtures = order_fixtures.TestReadonlyOrderQuote()
        self.addCleanup(self.fixtures.doCleanups)
        self.fixtures.setUp()
        self.addCleanup(self.fixtures.tearDown)
        self.cart = dict(service_type="Pickup", customer=self.fixtures.proposal["customer"],
                         items=[{key: row[key] for key in ("item_code", "qty")}
                                for row in self.fixtures.proposal["items"]])
        self.context = dict(self.fixtures.context)

    def run_quote(self):
        return quote.quote_cart(copy.deepcopy(self.cart), dict(self.context))

    def reject(self):
        with self.assertRaises(quote.QuoteUnavailable):
            self.run_quote()

    def test_pickup_exclusive_financial_contract(self):
        self.assertEqual(self.run_quote(), dict(
            currency="PEN", lines=[dict(item_code="DISH", qty=2, rate="100", amount="200"),
                                   dict(item_code="DRINK", qty=1, rate="50", amount="50")],
            tax="45", total="295", delivery_fee="0", net_total="250",
            taxes_and_charges=[dict(ordinal=1, rate="18", tax_amount="45", included_in_print_rate=0)]))

    def test_native_matrix_matches_legacy_and_includes_fee_once(self):
        fixture = self.fixtures
        fixture.docs["Sales Taxes and Charges Template", "TAXES"].taxes[0].rate = 10.5
        fixture.docs["Item Price", "PRICE-FEE"].price_list_rate = 6.5
        baseline = copy.deepcopy(fixture.docs)
        for charge in (False, True):
            for delivery in (False, True):
                for inclusive in (0, 1):
                    with self.subTest(charge=charge, delivery=delivery, inclusive=inclusive):
                        fixture.docs = copy.deepcopy(baseline)
                        if charge:
                            fixture.add_service_charge()
                        fixture.docs["POS Profile", "POS"].posa_tax_inclusive = inclusive
                        self.cart["service_type"] = "Delivery" if delivery else "Pickup"
                        if delivery:
                            self.cart["address"] = "ADDRESS"
                        else:
                            self.cart.pop("address", None)
                        before = copy.deepcopy(fixture.docs)
                        with patch.object(quote, "calculate_taxes_and_totals",
                                          wraps=order_fixtures.native_tax.calculate_taxes_and_totals) as engine:
                            result = self.run_quote()
                        self.assertEqual(engine.call_count, 1)
                        invoice = engine.call_args.args[0]
                        self.assertIsInstance(invoice, order_fixtures.POSInvoice)
                        self.assertEqual(sum(row.item_code == "FEE" for row in invoice.items), int(delivery))
                        self.assertEqual(len(invoice.items), 3 if delivery else 2)
                        self.assertEqual(result["delivery_fee"], "6.5" if delivery else "0")
                        self.assertEqual(len(result["lines"]), 2)
                        self.assertEqual(result["net_total"], quote._money(invoice.net_total))
                        self.assertEqual(result["taxes_and_charges"], [
                            dict(ordinal=index, rate=quote._money(row.rate),
                                 tax_amount=quote._money(row.tax_amount), included_in_print_rate=inclusive)
                            for index, row in enumerate(invoice.taxes, 1)])
                        self.assertEqual([row["rate"] for row in result["taxes_and_charges"]],
                                         ["10.5", "13"] if charge else ["10.5"])
                        exclusive = (("316.77" if delivery else "308.75") if charge
                                     else ("283.43" if delivery else "276.25"))
                        self.assertEqual(result["total"], ("256.5" if delivery else "250") if inclusive else exclusive)
                        proposal = {**fixture.proposal, **copy.deepcopy(self.cart)}
                        legacy = quote.quote_order(proposal, self.context)
                        self.assertEqual(set(legacy), {"currency", "lines", "tax", "total", "delivery_fee", "native_fingerprint"})
                        self.assertEqual({key: legacy[key] for key in legacy if key != "native_fingerprint"},
                                         {key: result[key] for key in legacy if key != "native_fingerprint"})
                        self.assertRegex(legacy["native_fingerprint"], r"^[0-9a-f]{64}$")
                        self.assertEqual(fixture.docs, before)

    def test_snapshot_and_flags_are_restored(self):
        cart, context = copy.deepcopy(self.cart), dict(self.context)
        frappe.flags.round_off_applicable_accounts = ["sentinel"]
        frappe.flags.round_row_wise_tax = "sentinel"
        first = self.run_quote()
        self.assertEqual(first, self.run_quote())
        self.assertEqual((self.cart, self.context), (cart, context))
        self.assertEqual(frappe.flags.round_off_applicable_accounts, ["sentinel"])
        self.assertEqual(frappe.flags.round_row_wise_tax, "sentinel")
        with patch.object(quote, "calculate_taxes_and_totals", side_effect=RuntimeError("synthetic failure")):
            with self.assertRaises(RuntimeError):
                self.run_quote()
        self.assertEqual(frappe.flags.round_row_wise_tax, "sentinel")
        self.assertEqual(frappe.flags.round_off_applicable_accounts, ["sentinel"])
        frappe.flags.clear()
        self.run_quote()
        self.assertNotIn("round_row_wise_tax", frappe.flags)
        self.assertNotIn("round_off_applicable_accounts", frappe.flags)

    def test_owned_readable_delivery_address_required(self):
        self.cart.update(service_type="Delivery", address="ADDRESS")
        address = self.fixtures.docs["Address", "ADDRESS"]
        original = copy.deepcopy(address)
        for mutation in (dict(denied=True), dict(disabled=1), dict(tax_category="SPECIAL"),
                         dict(links=[]), dict(links=[frappe._dict(link_doctype="Customer", link_name="OTHER")]),
                         dict(links=[frappe._dict(link_doctype="Supplier", link_name="CUSTOMER")])):
            with self.subTest(mutation=mutation):
                address.clear()
                address.update({**original, **mutation})
                self.reject()
        address.clear()
        address.update(original)
        self.assertEqual(self.run_quote()["delivery_fee"], "10")
        original_get_doc = self.fixtures.get_doc

        def missing_address(doctype, name):
            if doctype == "Address":
                raise frappe.DoesNotExistError("Synthetic missing address")
            return original_get_doc(doctype, name)

        with patch.object(frappe, "get_doc", side_effect=missing_address):
            self.reject()

    def test_read_permissions_cover_native_documents(self):
        self.cart.update(service_type="Delivery", address="ADDRESS")
        for key, document in self.fixtures.docs.items():
            if key[0] in {"User", "Currency"}:
                continue
            with self.subTest(document=key):
                document.denied = True
                self.reject()
                document.pop("denied")
        with patch.object(frappe, "has_permission", return_value=False):
            self.reject()

    def test_actor_company_profile_and_currency_scope(self):
        user = self.fixtures.docs["User", "api-test"]
        for actor, enabled, user_type in (("Guest", 1, "System User"), ("api-test", 0, "System User"),
                                          ("api-test", 1, "Website User")):
            with self.subTest(actor=actor, enabled=enabled, user_type=user_type):
                frappe.session.user = actor
                user.update(enabled=enabled, user_type=user_type)
                self.reject()
        frappe.session.user = "api-test"
        user.update(enabled=1, user_type="System User")
        for field, value in (("company", "FOREIGN"), ("profile_modified", "stale"),
                             ("selling_price_list", "FOREIGN"), ("currency", "USD")):
            with self.subTest(field=field), self.assertRaises(quote.QuoteUnavailable):
                quote.quote_cart(self.cart, {**self.context, field: value})
        profile = self.fixtures.docs["POS Profile", "POS"]
        original = dict(profile)
        for mutation in (dict(disabled=1), dict(company="FOREIGN"), dict(currency="USD"),
                         dict(applicable_for_users=[frappe._dict(user="OTHER")]),
                         dict(customer_groups=[frappe._dict(customer_group="OTHER")]),
                         dict(item_groups=[frappe._dict(item_group="OTHER")])):
            with self.subTest(mutation=mutation):
                profile.update(mutation)
                self.reject()
                profile.clear()
                profile.update(original)

    def test_services_customers_rules_and_categories_fail_closed(self):
        settings = self.fixtures.docs["Restaurant Company Settings", "SETTINGS"]
        for service, field in (("Pickup", "enable_pickup"), ("Delivery", "enable_delivery")):
            with self.subTest(service=service):
                self.cart["service_type"] = service
                if service == "Delivery":
                    self.cart["address"] = "ADDRESS"
                settings[field] = 0
                self.reject()
                settings[field] = 1
        customer = self.fixtures.docs["Customer", "CUSTOMER"]
        for field in ("disabled", "is_internal_customer", "tax_category", "tax_withholding_category"):
            with self.subTest(field=field):
                original = customer.get(field)
                customer[field] = 1
                self.reject()
                customer[field] = original
        for rule in ("Pricing Rule", "Tax Rule"):
            with self.subTest(rule=rule):
                self.fixtures.rules = {rule}
                self.reject()
        self.fixtures.rules = set()

    def test_item_and_ancestor_tax_guards(self):
        item = self.fixtures.docs["Item", "DISH"]
        original = copy.deepcopy(item)
        for mutation in (dict(disabled=1), dict(has_serial_no=1), dict(has_batch_no=1),
                         dict(has_variants=1), dict(variant_of="OTHER"), dict(is_fixed_asset=1),
                         dict(is_customer_provided_item=1), dict(is_sales_item=0),
                         dict(taxes=[frappe._dict(item_tax_template="SPECIAL")])):
            with self.subTest(mutation=mutation):
                item.update(mutation)
                self.reject()
                item.clear()
                item.update(original)
        self.fixtures.rules = {"Product Bundle"}
        self.reject()
        self.fixtures.rules = set()
        group = self.fixtures.docs["Item Group", "FOOD"]
        group.parent_item_group = "PARENT"
        self.fixtures.doc("Item Group", "PARENT", taxes=[frappe._dict(item_tax_template="SPECIAL")])
        self.reject()
        group.parent_item_group = "FOOD"
        self.reject()

    def test_native_prices_must_be_unambiguous_readable_and_supported(self):
        price = self.fixtures.docs["Item Price", "PRICE-DISH"]
        original = dict(price)
        for mutation in (dict(price_list_rate=0), dict(price_list_rate=-1), dict(price_list_rate="NaN"),
                         dict(currency="USD"), dict(uom="Box"), dict(packing_unit=3),
                         dict(valid_from="2030-01-02"), dict(valid_upto="2029-12-31"),
                         dict(customer="OTHER"), dict(price_list_rate="1.1234567")):
            with self.subTest(mutation=mutation):
                price.update(mutation)
                self.reject()
                price.clear()
                price.update(original)
        self.fixtures.docs.pop(("Item Price", "PRICE-DISH"))
        self.reject()
        self.fixtures.docs["Item Price", "PRICE-DISH"] = price
        self.fixtures.docs["Item Price", "DUPLICATE"] = order_fixtures.ReadDocument({**price, "name": "DUPLICATE"})
        self.reject()
        self.fixtures.docs.pop(("Item Price", "DUPLICATE"))
        with patch.object(quote, "get_price_list_rate_for", return_value=1):
            self.reject()

    def test_delivery_fee_cannot_be_product_or_stock(self):
        self.cart["items"][0]["item_code"] = "FEE"
        self.reject()
        self.cart["items"][0]["item_code"] = "DISH"
        self.cart.update(service_type="Delivery", address="ADDRESS")
        self.fixtures.docs["Item", "FEE"].is_stock_item = 1
        self.reject()
        self.fixtures.docs["Item", "FEE"].is_stock_item = 0
        self.fixtures.docs["Restaurant Company Settings", "SETTINGS"].delivery_fee_item = None
        self.reject()

    def test_native_tax_and_service_charge_support_limits(self):
        self.fixtures.add_service_charge()
        template = self.fixtures.docs["Sales Taxes and Charges Template", "TAXES"]
        row = template.taxes[-1]
        original = dict(row)
        for mutation in (dict(rate=-1), dict(rate=101), dict(rate="NaN"), dict(charge_type="Actual"),
                         dict(add_deduct_tax="Deduct"), dict(dont_recompute_tax=1)):
            with self.subTest(mutation=mutation):
                row.update(mutation)
                self.reject()
                row.clear()
                row.update(original)
        account = self.fixtures.docs["Account", "SERVICE"]
        original = dict(account)
        for mutation in (dict(company="OTHER"), dict(disabled=1), dict(is_group=1),
                         dict(root_type="Asset"), dict(report_type="Balance Sheet"), dict(account_type="Bank")):
            with self.subTest(mutation=mutation):
                account.update(mutation)
                self.reject()
                account.clear()
                account.update(original)
        template.taxes.append(copy.deepcopy(row))
        self.reject()
        template.taxes = []
        self.reject()

    def test_rounding_and_regional_override_guards(self):
        self.fixtures.docs["Company", "CO"].country = "COUNTRY"
        hooks = {"COUNTRY": {"erpnext.controllers.taxes_and_totals.update_itemised_tax_data": ["custom.override"]}}
        with patch.object(frappe, "get_hooks", return_value=hooks):
            self.reject()
        self.fixtures.disable_rounding = 0
        self.fixtures.docs["Item Price", "PRICE-DISH"].price_list_rate = 0.99
        self.fixtures.docs["Item Price", "PRICE-DRINK"].price_list_rate = 0.33
        self.reject()


if __name__ == "__main__":
    unittest.main()
