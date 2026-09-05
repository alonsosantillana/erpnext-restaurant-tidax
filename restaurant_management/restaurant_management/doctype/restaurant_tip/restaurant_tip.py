# Copyright (c) 2026, Quantum Bit Core and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cint, flt, getdate, now_datetime, nowtime, today


TIP_MANAGEMENT_ROLES = {
    "System Manager",
    "resto_admin",
    "resto_cajero",
    "Admin Resto",
    "Cajero",
}
TIP_ADMIN_ROLES = {"System Manager", "resto_admin", "Admin Resto"}


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

        if self.status != "Cancelled":
            duplicate = frappe.db.get_value(
                "Restaurant Tip",
                {
                    "pos_invoice": self.pos_invoice,
                    "status": ["!=", "Cancelled"],
                    "name": ["!=", self.name or ""],
                },
                "name",
            )
            if duplicate:
                frappe.throw(
                    _("Invoice {0} already has the active tip {1}").format(
                        self.pos_invoice, duplicate
                    )
                )


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


def _get_tip_cash_session(tip):
    if not frappe.db.exists("POS Invoice", tip.pos_invoice):
        return frappe._dict()

    rows = frappe.db.sql(
        """
        SELECT
            COALESCE(invoice.restaurant_pos_opening_entry, closing.pos_opening_entry) AS opening_entry,
            COALESCE(opening.pos_closing_entry, closing.name) AS closing_entry,
            opening.user AS cashier,
            closing.period_end_date AS closing_time
        FROM `tabPOS Invoice` invoice
        LEFT JOIN `tabPOS Opening Entry` opening
            ON opening.name = invoice.restaurant_pos_opening_entry
        LEFT JOIN `tabPOS Invoice Reference` reference
            ON reference.pos_invoice = invoice.name
            AND reference.parenttype = 'POS Closing Entry'
            AND reference.parentfield = 'pos_transactions'
        LEFT JOIN `tabPOS Closing Entry` closing
            ON closing.name = reference.parent
            AND closing.docstatus = 1
        WHERE invoice.name = %s
        LIMIT 1
        """,
        tip.pos_invoice,
        as_dict=True,
    )
    return rows[0] if rows else frappe._dict()


def _require_tip_management_permission(tip):
    roles = set(frappe.get_roles())
    if not roles.intersection(TIP_MANAGEMENT_ROLES):
        frappe.throw(
            _("Solo un cajero o administrador del restaurante puede gestionar una propina cobrada"),
            frappe.PermissionError,
        )

    if not frappe.has_permission("Company", "read", doc=tip.company):
        frappe.throw(
            _("No tiene permiso para gestionar propinas de la empresa {0}").format(tip.company),
            frappe.PermissionError,
        )

    cash_session = _get_tip_cash_session(tip)
    if cash_session.get("closing_entry") and not roles.intersection(TIP_ADMIN_ROLES):
        frappe.throw(
            _(
                "La apertura de caja {0} ya fue cerrada mediante {1}. "
                "Solo un administrador del restaurante puede modificar sus propinas."
            ).format(cash_session.opening_entry, cash_session.closing_entry),
            frappe.PermissionError,
        )
    return cash_session


def _validate_cancellation_reason(reason):
    reason = str(reason or "").strip()
    if len(reason) < 5:
        frappe.throw(
            _("Ingrese un motivo de anulación o rectificación de al menos 5 caracteres"),
            frappe.ValidationError,
        )
    return reason[:500]


def _get_locked_tip(tip_name):
    if not frappe.db.exists("Restaurant Tip", tip_name):
        frappe.throw(_("No existe la propina {0}").format(tip_name), frappe.DoesNotExistError)
    frappe.db.sql(
        "SELECT name FROM `tabRestaurant Tip` WHERE name = %s FOR UPDATE",
        tip_name,
    )
    return frappe.get_doc("Restaurant Tip", tip_name)



def _normalize_tip_names(tip_names):
    if isinstance(tip_names, str):
        tip_names = frappe.parse_json(tip_names)
    if not isinstance(tip_names, (list, tuple)):
        frappe.throw(_("Seleccione una o más propinas"))

    names = sorted({str(name).strip() for name in tip_names if str(name).strip()})
    if not names:
        frappe.throw(_("Seleccione una o más propinas"))
    if len(names) > 200:
        frappe.throw(_("Puede liquidar como máximo 200 propinas por operación"))
    return names


def _get_locked_tips(tip_names):
    placeholders = ", ".join(["%s"] * len(tip_names))
    locked = frappe.db.sql(
        "SELECT name FROM `tabRestaurant Tip` "
        f"WHERE name IN ({placeholders}) ORDER BY name FOR UPDATE",
        tuple(tip_names),
        as_dict=True,
    )
    locked_names = {row.name for row in locked}
    missing = [name for name in tip_names if name not in locked_names]
    if missing:
        frappe.throw(
            _("No existen las propinas: {0}").format(", ".join(missing)),
            frappe.DoesNotExistError,
        )
    return [frappe.get_doc("Restaurant Tip", name) for name in tip_names]


def _get_mode_of_payment_account(mode_of_payment, company):
    mode_of_payment = str(mode_of_payment or "").strip()
    if not mode_of_payment:
        frappe.throw(_("Seleccione el medio con el que se pagará al mozo"))

    if not frappe.db.exists("Mode of Payment", mode_of_payment):
        frappe.throw(_("No existe el modo de pago {0}").format(mode_of_payment))

    account = frappe.db.get_value(
        "Mode of Payment Account",
        {
            "parent": mode_of_payment,
            "parenttype": "Mode of Payment",
            "company": company,
        },
        "default_account",
    )
    if not account:
        frappe.throw(
            _("Configure una cuenta para el modo de pago {0} y la empresa {1}").format(
                mode_of_payment, company
            )
        )
    _validate_account(
        account,
        company,
        expected_root_type="Asset",
        label=_("Cuenta de pago"),
    )
    return account


def _validate_tip_settlement(tips, posting_date):
    first = tips[0]
    dimensions = {
        "company": first.company,
        "waiter": first.waiter,
        "liability_account": first.liability_account,
    }
    sessions = []
    for tip in tips:
        if tip.status != "Collected" or tip.get("settlement_journal_entry"):
            frappe.throw(
                _("La propina {0} no está pendiente de pago al mozo").format(tip.name)
            )
        for fieldname, expected in dimensions.items():
            if tip.get(fieldname) != expected:
                frappe.throw(
                    _("Todas las propinas deben pertenecer al mismo mozo, empresa y cuenta por pagar")
                )
        if not tip.collection_journal_entry:
            frappe.throw(
                _("La propina {0} no tiene asiento de recepción").format(tip.name)
            )
        if frappe.db.get_value(
            "Journal Entry", tip.collection_journal_entry, "docstatus"
        ) != 1:
            frappe.throw(
                _("El asiento de recepción {0} no está enviado").format(
                    tip.collection_journal_entry
                )
            )
        session = _get_tip_cash_session(tip)
        if not session.get("closing_entry"):
            frappe.throw(
                _("La propina {0} todavía no pertenece a un cierre POS enviado").format(tip.name)
            )
        sessions.append(session)

    closing_entries = {session.closing_entry for session in sessions}
    if len(closing_entries) != 1:
        frappe.throw(_("Todas las propinas deben pertenecer al mismo cierre POS"))

    closing_time = sessions[0].get("closing_time")
    if closing_time and getdate(posting_date) < getdate(closing_time):
        frappe.throw(_("La fecha de pago no puede ser anterior al cierre POS"))

    roles = set(frappe.get_roles())
    if not roles.intersection(TIP_MANAGEMENT_ROLES):
        frappe.throw(
            _("Solo un cajero o administrador del restaurante puede pagar propinas"),
            frappe.PermissionError,
        )
    if not frappe.has_permission("Company", "read", doc=first.company):
        frappe.throw(
            _("No tiene permiso para gestionar propinas de la empresa {0}").format(first.company),
            frappe.PermissionError,
        )
    if not roles.intersection(TIP_ADMIN_ROLES):
        cashiers = {session.get("cashier") for session in sessions}
        if cashiers != {frappe.session.user}:
            frappe.throw(
                _("El cajero solo puede pagar propinas de sus propios cierres POS"),
                frappe.PermissionError,
            )

    _validate_account(
        first.liability_account,
        first.company,
        expected_root_type="Liability",
        label=_("Cuenta de propinas por pagar"),
    )
    return frappe._dict(
        company=first.company,
        waiter=first.waiter,
        liability_account=first.liability_account,
        closing_entry=sessions[0].closing_entry,
        total=flt(sum(flt(tip.amount) for tip in tips), 2),
    )


@frappe.whitelist(methods=["POST"])
def settle_restaurant_tips(tip_names, mode_of_payment, posting_date=None):
    names = _normalize_tip_names(tip_names)
    posting_date = posting_date or today()

    savepoint = "settle_restaurant_tips"
    frappe.db.savepoint(savepoint)
    try:
        tips = _get_locked_tips(names)
        context = _validate_tip_settlement(tips, posting_date)
        payment_account = _get_mode_of_payment_account(
            mode_of_payment, context.company
        )

        journal_entry = frappe.new_doc("Journal Entry")
        journal_entry.company = context.company
        journal_entry.posting_date = posting_date
        journal_entry.voucher_type = "Journal Entry"
        journal_entry.user_remark = _(
            "Pago consolidado de {0} propina(s) al mozo {1}; cierre POS {2}"
        ).format(len(tips), context.waiter, context.closing_entry)
        for tip in tips:
            journal_entry.append(
                "accounts",
                {
                    "account": context.liability_account,
                    "debit_in_account_currency": tip.amount,
                    "credit_in_account_currency": 0,
                    "reference_type": "Journal Entry",
                    "reference_name": tip.collection_journal_entry,
                    "user_remark": _("Propina {0} / comprobante {1}").format(
                        tip.name, tip.pos_invoice
                    ),
                },
            )
        journal_entry.append(
            "accounts",
            {
                "account": payment_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": context.total,
            },
        )
        journal_entry.flags.ignore_permissions = True
        journal_entry.insert()
        journal_entry.submit()

        settled_on = now_datetime()
        for tip in tips:
            frappe.db.set_value(
                "Restaurant Tip",
                tip.name,
                {
                    "status": "Settled",
                    "settlement_journal_entry": journal_entry.name,
                    "settlement_mode_of_payment": mode_of_payment,
                    "settlement_account": payment_account,
                    "settled_by": frappe.session.user,
                    "settled_on": settled_on,
                },
                update_modified=True,
            )
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        raise

    return {
        "journal_entry": journal_entry.name,
        "waiter": context.waiter,
        "closing_entry": context.closing_entry,
        "tip_count": len(tips),
        "total": context.total,
    }


def restore_tips_for_cancelled_settlement(doc, method=None):
    tip_names = frappe.get_all(
        "Restaurant Tip",
        filters={
            "settlement_journal_entry": doc.name,
            "status": "Settled",
        },
        pluck="name",
    )
    for tip_name in tip_names:
        frappe.db.set_value(
            "Restaurant Tip",
            tip_name,
            {
                "status": "Collected",
                "settlement_journal_entry": None,
                "settlement_mode_of_payment": None,
                "settlement_account": None,
                "settled_by": None,
                "settled_on": None,
            },
            update_modified=True,
        )


def _cancel_tip_document(tip, reason):
    if tip.status == "Cancelled":
        frappe.throw(_("La propina {0} ya está anulada").format(tip.name))
    if tip.status == "Settled":
        frappe.throw(
            _("La propina {0} ya fue liquidada. Primero debe revertirse su liquidación.").format(tip.name)
        )

    if tip.collection_journal_entry:
        journal_entry = frappe.get_doc("Journal Entry", tip.collection_journal_entry)
        if journal_entry.docstatus == 1:
            journal_entry.flags.ignore_permissions = True
            journal_entry.cancel()

    values = {
        "status": "Cancelled",
        "cancellation_reason": reason,
        "cancelled_by": frappe.session.user,
        "cancelled_on": now_datetime(),
        "error_message": None,
    }
    frappe.db.set_value("Restaurant Tip", tip.name, values, update_modified=True)
    tip.update(values)
    return tip


@frappe.whitelist(methods=["POST"])
def cancel_restaurant_tip(tip_name, reason):
    tip = _get_locked_tip(tip_name)
    _require_tip_management_permission(tip)
    reason = _validate_cancellation_reason(reason)

    savepoint = "cancel_restaurant_tip"
    frappe.db.savepoint(savepoint)
    try:
        _cancel_tip_document(tip, reason)
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        raise

    return {
        "tip": tip.name,
        "status": tip.status,
        "pos_invoice": tip.pos_invoice,
    }


@frappe.whitelist(methods=["POST"])
def rectify_restaurant_tip(tip_name, new_amount, reason, confirm_adjustment=0):
    tip = _get_locked_tip(tip_name)
    _require_tip_management_permission(tip)
    reason = _validate_cancellation_reason(reason)
    amount = flt(new_amount, 2)
    if amount <= 0:
        frappe.throw(_("El nuevo importe de la propina debe ser mayor que cero"))
    if abs(amount - flt(tip.amount, 2)) < 0.005:
        frappe.throw(_("El nuevo importe debe ser diferente de la propina actual"))
    if not cint(confirm_adjustment):
        frappe.throw(
            _("Confirme que la diferencia fue cobrada o devuelta al cliente"),
            frappe.ValidationError,
        )

    savepoint = "rectify_restaurant_tip"
    frappe.db.savepoint(savepoint)
    try:
        _cancel_tip_document(tip, reason)
        replacement = frappe.get_doc(
            {
                "doctype": "Restaurant Tip",
                "company": tip.company,
                "posting_date": tip.posting_date,
                "posting_time": tip.posting_time,
                "table_order": tip.table_order,
                "pos_invoice": tip.pos_invoice,
                "pos_profile": tip.pos_profile,
                "amount": amount,
                "mode_of_payment": tip.mode_of_payment,
                "collection_account": tip.collection_account,
                "liability_account": tip.liability_account,
                "status": "Pending Accounting",
                "waiter": tip.waiter,
                "corrects_tip": tip.name,
            }
        ).insert(ignore_permissions=True)
        replacement = post_tip_collection(replacement)
        if replacement.status != "Collected":
            frappe.throw(
                _("No se pudo contabilizar la propina corregida. La rectificación fue revertida.")
            )
        frappe.db.set_value(
            "Restaurant Tip",
            tip.name,
            "replaced_by",
            replacement.name,
            update_modified=True,
        )
    except Exception:
        frappe.db.rollback(save_point=savepoint)
        raise

    return {
        "tip": replacement.name,
        "status": replacement.status,
        "previous_tip": tip.name,
        "pos_invoice": replacement.pos_invoice,
    }


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
    tip_names = frappe.get_all(
        "Restaurant Tip",
        filters={"pos_invoice": doc.name, "status": ["!=", "Cancelled"]},
        pluck="name",
    )
    for tip_name in tip_names:
        tip = frappe.get_doc("Restaurant Tip", tip_name)
        _cancel_tip_document(
            tip,
            _("La Factura POS {0} fue anulada").format(doc.name),
        )
