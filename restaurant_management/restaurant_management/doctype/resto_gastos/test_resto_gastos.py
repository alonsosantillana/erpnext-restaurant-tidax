from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from restaurant_management.restaurant_management.doctype.resto_gastos.resto_gastos import (
    RestoGastos,
    _validate_payment_account,
)


class TestRestoGastos(FrappeTestCase):
    def test_server_recalculates_total(self):
        doc = MagicMock()
        doc.gto_detalle = [
            frappe._dict(importe_gto=10.25),
            frappe._dict(importe_gto=4.75),
        ]
        doc.precision.return_value = 2

        RestoGastos._calculate_total(doc)

        self.assertEqual(doc.gto_total, 15.0)

    @patch(
        "restaurant_management.restaurant_management.doctype.resto_gastos.resto_gastos.frappe.db.get_value"
    )
    def test_rejects_item_outside_expense_group(self, get_value):
        get_value.return_value = frappe._dict(
            item_name="CEVICHE", item_group="PLATOS", disabled=0
        )
        row = MagicMock(idx=1, item_gto="PLT-001", importe_gto=10)
        doc = MagicMock(gto_detalle=[row])

        self.assertRaises(
            frappe.ValidationError,
            RestoGastos._validate_details,
            doc,
        )

    @patch(
        "restaurant_management.restaurant_management.doctype.resto_gastos.resto_gastos.frappe.db.get_value"
    )
    def test_rejects_non_positive_amount(self, get_value):
        get_value.return_value = frappe._dict(
            item_name="Caja chica", item_group="GASTOS", disabled=0
        )
        row = MagicMock(idx=1, item_gto="GTO-001", importe_gto=0)
        row.precision.return_value = 2
        doc = MagicMock(gto_detalle=[row])

        self.assertRaises(
            frappe.ValidationError,
            RestoGastos._validate_details,
            doc,
        )

    @patch(
        "restaurant_management.restaurant_management.doctype.resto_gastos.resto_gastos._get_opening"
    )
    def test_rejects_opening_from_another_company(self, get_opening):
        get_opening.return_value = frappe._dict(
            name="POS-OPE-B",
            company="Company B",
            pos_profile="POS-B",
            status="Open",
            docstatus=1,
        )
        doc = MagicMock(company="Company A", pos_opening_entry="POS-OPE-B")

        self.assertRaises(
            frappe.ValidationError,
            RestoGastos._validate_opening,
            doc,
        )

    @patch(
        "restaurant_management.restaurant_management.doctype.resto_gastos.resto_gastos.frappe.db.get_value"
    )
    def test_rejects_payment_account_from_another_company(self, get_value):
        get_value.return_value = frappe._dict(
            company="Company B",
            root_type="Asset",
            is_group=0,
            disabled=0,
        )

        self.assertRaises(
            frappe.ValidationError,
            _validate_payment_account,
            "Cash - B",
            "Company A",
        )

    @patch(
        "restaurant_management.restaurant_management.doctype.resto_gastos.resto_gastos.frappe.db.exists"
    )
    def test_rejects_cancellation_after_pos_closing(self, exists):
        exists.return_value = "POS-CLO-1"
        doc = MagicMock(pos_opening_entry="POS-OPE-1")

        self.assertRaises(
            frappe.ValidationError,
            RestoGastos.before_cancel,
            doc,
        )
