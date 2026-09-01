# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt

from restaurant_management.restaurant_management.company_settings import (
    get_user_restaurant_company,
)
from restaurant_management.restaurant_management.pos_series import (
    get_company_expense_series,
)


EXPENSE_ITEM_GROUP = "GASTOS"


class RestoGastos(Document):
    def autoname(self):
        self.company = self.company or get_user_restaurant_company()
        if not self.company:
            frappe.throw(_("Company is required to resolve the expense series"))

        self.naming_series = get_company_expense_series(self.company)
        self.name = make_autoname(self.naming_series, doc=self)

    def before_validate(self):
        self.company = self.company or get_user_restaurant_company()
        if self.pos_opening_entry:
            opening = _get_opening(self.pos_opening_entry)
            self.pos_profile = opening.pos_profile
        if self.company and self.mode_of_payment:
            self.payment_account = _get_payment_account(
                self.company, self.mode_of_payment
            )
        self._calculate_total()

    def validate(self):
        self._validate_company_access()
        opening = self._validate_opening()
        self._validate_payment_context(opening)
        self._validate_details()
        self._calculate_total()

    def before_cancel(self):
        closing_entry = frappe.db.exists(
            "POS Closing Entry",
            {"pos_opening_entry": self.pos_opening_entry, "docstatus": 1},
        )
        if closing_entry:
            frappe.throw(
                _(
                    "Expense cannot be cancelled because POS Closing Entry {0} already includes it"
                ).format(closing_entry),
                title=_("POS already closed"),
            )

        opening_status = frappe.db.get_value(
            "POS Opening Entry", self.pos_opening_entry, "status"
        )
        if opening_status != "Open":
            frappe.throw(
                _("Expense cannot be cancelled after its POS Opening Entry is closed"),
                title=_("POS already closed"),
            )

    def _validate_company_access(self):
        if not self.company:
            frappe.throw(_("Company is required"))
        if not frappe.has_permission("Company", "read", doc=self.company):
            frappe.throw(
                _("Not permitted to use Company {0}").format(self.company),
                frappe.PermissionError,
            )

    def _validate_opening(self):
        if not self.pos_opening_entry:
            frappe.throw(_("POS Opening Entry is required"))

        opening = _get_opening(self.pos_opening_entry)
        if opening.company != self.company:
            frappe.throw(
                _("POS Opening Entry {0} does not belong to company {1}").format(
                    self.pos_opening_entry, self.company
                )
            )
        if opening.docstatus != 1 or opening.status != "Open":
            frappe.throw(
                _("POS Opening Entry {0} must be submitted and open").format(
                    self.pos_opening_entry
                )
            )

        self.pos_profile = opening.pos_profile
        return opening

    def _validate_payment_context(self, opening):
        if not self.mode_of_payment:
            frappe.throw(_("Mode of Payment is required"))

        opening_method = frappe.db.exists(
            "POS Opening Entry Detail",
            {
                "parent": opening.name,
                "parenttype": "POS Opening Entry",
                "mode_of_payment": self.mode_of_payment,
            },
        )
        profile_method = frappe.db.exists(
            "POS Payment Method",
            {
                "parent": opening.pos_profile,
                "parenttype": "POS Profile",
                "mode_of_payment": self.mode_of_payment,
            },
        )
        if not opening_method or not profile_method:
            frappe.throw(
                _("Mode of Payment {0} is not available in POS opening {1}").format(
                    self.mode_of_payment, opening.name
                )
            )

        expected_account = _get_payment_account(
            self.company, self.mode_of_payment, required=True
        )
        if self.payment_account and self.payment_account != expected_account:
            frappe.throw(
                _("Payment Account does not match Mode of Payment {0}").format(
                    self.mode_of_payment
                )
            )
        self.payment_account = expected_account
        _validate_payment_account(self.payment_account, self.company)

    def _validate_details(self):
        if not self.gto_detalle:
            frappe.throw(_("Add at least one expense detail"))

        for row in self.gto_detalle:
            item = frappe.db.get_value(
                "Item",
                row.item_gto,
                ["item_name", "item_group", "disabled"],
                as_dict=True,
            )
            if not item or item.disabled:
                frappe.throw(
                    _("Row {0}: select an enabled expense Item").format(row.idx)
                )
            if item.item_group != EXPENSE_ITEM_GROUP:
                frappe.throw(
                    _("Row {0}: Item must belong to group {1}").format(
                        row.idx, EXPENSE_ITEM_GROUP
                    )
                )

            amount = flt(row.importe_gto, row.precision("importe_gto"))
            if amount <= 0:
                frappe.throw(
                    _("Row {0}: amount must be greater than zero").format(row.idx)
                )
            row.importe_gto = amount
            row.gasto_gto = item.item_name
            row.grupo_gto = item.item_group

    def _calculate_total(self):
        total = sum(flt(row.importe_gto) for row in self.gto_detalle or [])
        self.gto_total = flt(total, self.precision("gto_total"))


def _get_opening(opening_name):
    opening = frappe.db.get_value(
        "POS Opening Entry",
        opening_name,
        ["name", "company", "pos_profile", "status", "docstatus"],
        as_dict=True,
    )
    if not opening:
        frappe.throw(_("POS Opening Entry {0} does not exist").format(opening_name))
    return opening


def _get_payment_account(company, mode_of_payment, required=False):
    account = frappe.db.get_value(
        "Mode of Payment Account",
        {
            "parent": mode_of_payment,
            "parenttype": "Mode of Payment",
            "company": company,
        },
        "default_account",
    )
    if required and not account:
        frappe.throw(
            _("Configure an account for payment method {0} and company {1}").format(
                mode_of_payment, company
            )
        )
    return account


def _validate_payment_account(account_name, company):
    account = frappe.db.get_value(
        "Account",
        account_name,
        ["company", "root_type", "is_group", "disabled"],
        as_dict=True,
    )
    if not account or account.disabled:
        frappe.throw(_("Payment Account must be an enabled Account"))
    if account.company != company:
        frappe.throw(
            _("Payment Account must belong to company {0}").format(company)
        )
    if account.root_type != "Asset" or account.is_group:
        frappe.throw(_("Payment Account must be a non-group Asset account"))


@frappe.whitelist()
def get_opening_context(pos_opening_entry):
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)

    opening_doc = frappe.get_doc("POS Opening Entry", pos_opening_entry)
    opening_doc.check_permission("read")
    opening = _get_opening(pos_opening_entry)
    if opening.docstatus != 1 or opening.status != "Open":
        frappe.throw(_("Select a submitted and open POS Opening Entry"))

    profile_modes = set(
        frappe.get_all(
            "POS Payment Method",
            filters={
                "parent": opening.pos_profile,
                "parenttype": "POS Profile",
            },
            pluck="mode_of_payment",
        )
    )
    opening_modes = frappe.get_all(
        "POS Opening Entry Detail",
        filters={
            "parent": opening.name,
            "parenttype": "POS Opening Entry",
        },
        pluck="mode_of_payment",
    )
    modes = [mode for mode in opening_modes if mode in profile_modes]
    accounts = {
        mode: _get_payment_account(opening.company, mode) for mode in modes
    }
    return {
        "company": opening.company,
        "pos_profile": opening.pos_profile,
        "modes_of_payment": modes,
        "payment_accounts": accounts,
    }
