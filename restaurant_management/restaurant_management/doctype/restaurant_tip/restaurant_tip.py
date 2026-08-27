# Copyright (c) 2026, Quantum Bit Core and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, nowtime, today


class RestaurantTip(Document):
    def autoname(self):
        abbreviation = frappe.get_cached_value("Company", self.company, "abbr")
        self.name = make_autoname("TIP-{0}-.YYYY.-.#####".format(abbreviation))

    def validate(self):
        if flt(self.amount) <= 0:
            frappe.throw(_("Tip amount must be greater than zero"))
        _validate_account(
            self.collection_account,
            self.company,
            expected_root_type="Asset",
            label=_("Collection Account"),
        )
        _validate_account(
            self.liability_account,
            self.company,
            expected_root_type="Liability",
            label=_("Tips Payable Account"),
        )

        linked_companies = {
            frappe.db.get_value("Table Order", self.table_order, "company"),
            frappe.db.get_value("POS Invoice", self.pos_invoice, "company"),
            frappe.db.get_value("POS Profile", self.pos_profile, "company"),
        }
        linked_companies.discard(None)
        if linked_companies != {self.company}:
            frappe.throw(_("Tip documents must belong to the same company"))


def _validate_account(account_name, company, expected_root_type, label):
    account = frappe.db.get_value(
        "Account",
        account_name,
        ["company", "root_type", "is_group", "disabled"],
        as_dict=True,
    )
    if not account or account.disabled:
        frappe.throw(_("{0} must be an enabled Account").format(label))
    if account.company != company:
        frappe.throw(_("{0} must belong to company {1}").format(label, company))
    if account.root_type != expected_root_type or account.is_group:
        frappe.throw(
            _("{0} must be a non-group {1} account").format(
                label, expected_root_type
            )
        )


def validate_tip_request(order, tip_amount=0, tip_mode_of_payment=None):
    amount = flt(tip_amount, 2)
    if amount < 0:
        frappe.throw(_("Tip amount cannot be negative"))
    if not amount:
        return None

    settings = frappe.get_doc(
        "Restaurant Company Settings",
        frappe.db.get_value(
            "Restaurant Company Settings", {"company": order.company}, "name"
        ),
    )
    if not settings.get("enable_tips"):
        frappe.throw(_("Tips are not enabled for company {0}").format(order.company))
    if not settings.get("tip_payable_account"):
        frappe.throw(_("Configure the Tips Payable Account for {0}").format(order.company))

    mode_of_payment = str(tip_mode_of_payment or "").strip()
    if not mode_of_payment:
        frappe.throw(_("Select the tip collection method"))

    profile_method = frappe.db.exists(
        "POS Payment Method",
        {
            "parent": order.pos_profile,
            "parenttype": "POS Profile",
            "mode_of_payment": mode_of_payment,
        },
    )
    if not profile_method:
        frappe.throw(
            _("Collection method {0} is not available in POS Profile {1}").format(
                mode_of_payment, order.pos_profile
            )
        )

    collection_account = frappe.db.get_value(
        "Mode of Payment Account",
        {
            "parent": mode_of_payment,
            "parenttype": "Mode of Payment",
            "company": order.company,
        },
        "default_account",
    )
    if not collection_account:
        frappe.throw(
            _("Configure an account for payment method {0} and company {1}").format(
                mode_of_payment, order.company
            )
        )

    _validate_account(
        collection_account,
        order.company,
        expected_root_type="Asset",
        label=_("Collection Account"),
    )
    _validate_account(
        settings.tip_payable_account,
        order.company,
        expected_root_type="Liability",
        label=_("Tips Payable Account"),
    )

    return frappe._dict(
        amount=amount,
        mode_of_payment=mode_of_payment,
        collection_account=collection_account,
        liability_account=settings.tip_payable_account,
    )


def create_tip_record(order, invoice, tip_context):
    if not tip_context:
        return None

    waiter = order.get("cambio_mozo") or order.owner
    return frappe.get_doc(
        {
            "doctype": "Restaurant Tip",
            "company": order.company,
            "posting_date": invoice.posting_date or today(),
            "posting_time": invoice.posting_time or nowtime(),
            "table_order": order.name,
            "pos_invoice": invoice.name,
            "pos_profile": order.pos_profile,
            "amount": tip_context.amount,
            "mode_of_payment": tip_context.mode_of_payment,
            "collection_account": tip_context.collection_account,
            "liability_account": tip_context.liability_account,
            "status": "Pending Accounting",
            "waiter": waiter,
        }
    ).insert(ignore_permissions=True)


def post_tip_collection(tip):
    if not tip or tip.status != "Pending Accounting":
        return tip

    savepoint = "restaurant_tip_accounting"
    frappe.db.savepoint(savepoint)
    try:
        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.company = tip.company
        journal_entry.posting_date = tip.posting_date
        journal_entry.voucher_type = "Journal Entry"
        journal_entry.user_remark = _(
            "Tip collected for order {0} / invoice {1}"
        ).format(tip.table_order, tip.pos_invoice)
        journal_entry.append(
            "accounts",
            {
                "account": tip.collection_account,
                "debit_in_account_currency": tip.amount,
                "credit_in_account_currency": 0,
            },
        )
        journal_entry.append(
            "accounts",
            {
                "account": tip.liability_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": tip.amount,
            },
        )
        journal_entry.flags.ignore_permissions = True
        journal_entry.insert()
        journal_entry.submit()

        tip.db_set("collection_journal_entry", journal_entry.name, update_modified=False)
        tip.db_set("status", "Collected", update_modified=False)
        tip.db_set("error_message", None, update_modified=False)
        tip.collection_journal_entry = journal_entry.name
        tip.status = "Collected"
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        error = frappe.get_traceback()
        frappe.db.set_value(
            "Restaurant Tip",
            tip.name,
            {
                "status": "Pending Accounting",
                "error_message": error[-2000:],
            },
            update_modified=False,
        )
        frappe.log_error(error, _("Restaurant tip accounting failed"))
        tip.status = "Pending Accounting"

    return tip


def cancel_tip_for_invoice(doc, method=None):
    tip_name = frappe.db.get_value("Restaurant Tip", {"pos_invoice": doc.name}, "name")
    if not tip_name:
        return

    tip = frappe.get_doc("Restaurant Tip", tip_name)
    if tip.collection_journal_entry:
        journal_entry = frappe.get_doc("Journal Entry", tip.collection_journal_entry)
        if journal_entry.docstatus == 1:
            journal_entry.flags.ignore_permissions = True
            journal_entry.cancel()

    tip.db_set("status", "Cancelled", update_modified=False)
    tip.db_set("error_message", None, update_modified=False)
