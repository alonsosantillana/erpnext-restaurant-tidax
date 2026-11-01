"""Pure v16 compatibility checks: no framework import, DB or external services."""
import ast
from collections import defaultdict
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]

class AttrDict(dict):
    def __getattr__(self, key):
        return self.get(key)

def load_functions(filename, names, namespace):
    tree = ast.parse((ROOT / filename).read_text())
    nodes = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
    assert len(nodes) == len(names)
    for node in nodes:
        node.decorator_list = []
    namespace.setdefault("__builtins__", __builtins__)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), filename, "exec"), namespace)
    return namespace


class TestV16PosContracts(unittest.TestCase):
    def test_legacy_contract_only_returns_complete_pos_documents(self):
        native = types.SimpleNamespace(get_invoices=Mock(return_value={
            "invoices": [{"doctype": "Sales Invoice", "name": "SI"}, {"doctype": "POS Invoice", "name": "POS"}],
        }))
        doc = types.SimpleNamespace(as_dict=lambda: {"name": "POS", "items": [{"item_code": "ITEM"}]})
        get_doc = Mock(return_value=doc)
        ns = load_functions("restaurant_management/restaurant_management/pos_closing.py", ["erpnext_get_pos_invoices"], {
            "native_pos_closing": native, "frappe": types.SimpleNamespace(get_doc=get_doc),
        })
        result = ns["erpnext_get_pos_invoices"]("start", "end", "profile", "user")
        self.assertEqual(result, [{"name": "POS", "items": [{"item_code": "ITEM"}]}])
        get_doc.assert_called_once_with("POS Invoice", "POS")

    def test_nonrestaurant_native_payload_is_unchanged(self):
        payload = {"invoices": [], "payments": ["native"], "taxes": []}
        native = types.SimpleNamespace(get_invoices=Mock(return_value=payload))
        scope = Mock()
        ns = load_functions("restaurant_management/restaurant_management/pos_closing.py", ["get_invoices"], {
            "native_pos_closing": native, "_is_restaurant_pos_profile": lambda profile: False,
            "get_pos_invoices": scope,
        })
        self.assertIs(ns["get_invoices"]("start", "end", "profile", "user"), payload)
        scope.assert_not_called()

    def test_restaurant_scope_and_native_aggregation_are_preserved(self):
        original_rows = [AttrDict(doctype="POS Invoice", name="wrong-session", timestamp="2026-01-01 00:00:00"),
            AttrDict(doctype="Sales Invoice", name="SI", timestamp="2026-01-01 02:00:00")]
        payload = {"invoices": original_rows, "payments": ["old"], "taxes": ["old"]}
        native = types.SimpleNamespace(get_invoices=Mock(return_value=payload),
            get_payments=Mock(return_value=["native payments"]), get_taxes=Mock(return_value=["native taxes"]))
        scoped = [{"name": "right-session", "posting_date": "2026-01-01", "posting_time": "01:00:00", "grand_total": 123}]
        ns = load_functions("restaurant_management/restaurant_management/pos_closing.py", ["get_invoices", "_v16_pos_invoice_row"], {
            "native_pos_closing": native, "_is_restaurant_pos_profile": lambda profile: True,
            "get_pos_invoices": lambda *args: scoped,
            "frappe": types.SimpleNamespace(_dict=AttrDict, db=types.SimpleNamespace(get_single_value=lambda *args: "POS Invoice")), "get_datetime": lambda value: value,
        })
        actual = ns["get_invoices"]("start", "end", "profile", "user")
        self.assertEqual([row["name"] for row in actual["invoices"]], ["right-session", "SI"])
        self.assertEqual(set(actual), {"invoices", "payments", "taxes"})
        self.assertEqual(actual["payments"], ["native payments"])
        self.assertEqual(actual["taxes"], ["native taxes"])
        native.get_payments.assert_called_once_with(actual["invoices"])
        native.get_taxes.assert_called_once_with(actual["invoices"])
        self.assertIs(payload["invoices"], original_rows)
        self.assertEqual(payload["payments"], ["old"])


    def test_sales_invoice_mode_does_not_fetch_or_expose_pos_documents(self):
        payload = {"invoices": [{"doctype": "Sales Invoice", "name": "SI"}], "payments": [], "taxes": []}
        scope = Mock()
        ns = load_functions("restaurant_management/restaurant_management/pos_closing.py", ["get_invoices"], {
            "native_pos_closing": types.SimpleNamespace(get_invoices=Mock(return_value=payload)),
            "_is_restaurant_pos_profile": lambda profile: True, "get_pos_invoices": scope,
            "frappe": types.SimpleNamespace(db=types.SimpleNamespace(get_single_value=lambda *args: "Sales Invoice")),
        })
        self.assertIs(ns["get_invoices"]("start", "end", "profile", "user"), payload)
        scope.assert_not_called()

    def closing_environment(self, invoice_opening):
        invoice = AttrDict(consolidated_invoice=None, pos_profile="profile", docstatus=1,
            owner="other-cashier", restaurant_pos_opening_entry=invoice_opening)
        def throw(messages, **kwargs):
            raise ValueError(messages)
        namespace = {"ERPNextPOSClosingEntry": AttrDict, "_is_restaurant_pos_profile": lambda profile: True,
            "frappe": types.SimpleNamespace(db=types.SimpleNamespace(get_value=lambda *args, **kwargs: invoice),
                throw=throw, bold=lambda value: value), "_": lambda value: value}
        tree = ast.parse((ROOT / "restaurant_management/restaurant_management/pos_closing.py").read_text())
        node = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "RestaurantPOSClosingEntry")
        exec(compile(ast.Module(body=[node], type_ignores=[]), "RestaurantPOSClosingEntry", "exec"), namespace)
        return namespace["RestaurantPOSClosingEntry"](pos_profile="profile", user="cashier",
            pos_opening_entry="opening", pos_invoices=[AttrDict(pos_invoice="POS", idx=1)])

    def test_v16_invoice_table_accepts_matching_restaurant_opening(self):
        self.closing_environment("opening").validate_pos_invoices()

    def test_v16_invoice_table_rejects_another_restaurant_opening(self):
        with self.assertRaises(ValueError):
            self.closing_environment("another-opening").validate_pos_invoices()


    def test_parentfield_selector_supports_both_schema_versions(self):
        namespace = load_functions("restaurant_management/restaurant_management/report_utils.py", ["get_pos_transactions_field"], {
            "POS_TRANSACTIONS_FIELD": "pos_transactions",
        })
        self.assertEqual(namespace["get_pos_transactions_field"]("15.100.0"), "pos_transactions")
        self.assertEqual(namespace["get_pos_transactions_field"]("16.0.0"), "pos_invoices")
        self.assertEqual(namespace["get_pos_transactions_field"]("17.0.0-dev"), "pos_invoices")

    def test_v16_expense_sales_source_uses_the_renamed_table(self):
        payment = AttrDict(amount=10, account="cash", mode_of_payment="Cash")
        invoice = AttrDict(payments=[payment], account_for_change_amount="cash", change_amount=2)
        get_doc = Mock(return_value=invoice)
        namespace = load_functions("restaurant_management/restaurant_management/pos_closing_expenses.py", ["_get_sales_amounts"], {
            "frappe": types.SimpleNamespace(get_doc=get_doc), "defaultdict": defaultdict, "flt": float,
        })
        closing = AttrDict(pos_invoices=[AttrDict(pos_invoice="POS")])
        self.assertEqual(namespace["_get_sales_amounts"](closing), {"Cash": 8.0})
        get_doc.assert_called_once_with("POS Invoice", "POS")

if __name__ == "__main__":
    unittest.main()
