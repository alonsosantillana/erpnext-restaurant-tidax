"""Bounded internal R9E.2 quotes. No order, invoice, price or FX writes.

Unsupported pricing raises QuoteUnavailable for handoff. This is not an HTTP
endpoint or authority to admit an order; TIX's adapter remains default-off.
"""

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import frappe
from frappe.utils import cint, getdate, today
from erpnext.accounts.doctype.pos_invoice.pos_invoice import POSInvoice
from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
from erpnext.stock.get_item_details import get_price_list_rate_for

from restaurant_management.restaurant_management.company_settings import (
    get_restaurant_settings,
    get_user_restaurant_company,
)


class QuoteUnavailable(frappe.ValidationError):
    """The cart needs manual pricing; do not substitute zero or stale totals."""


def _require(condition):
    if not condition:
        raise QuoteUnavailable("Native read-only quote unavailable; manual review required")


def _reference(value):
    _require(isinstance(value, str) and 0 < len(value) <= 140)
    _require(value == value.strip() and not any(ord(c) < 32 for c in value))
    return value


def _decimal(value, maximum=Decimal("999999999.999999")):
    _require(not isinstance(value, bool) and isinstance(value, (str, int, float, Decimal)))
    _require(len(str(value)) <= 40)
    try:
        number = Decimal(str(value))
        _require(number.is_finite() and 0 <= number <= maximum)
        rounded = number.quantize(Decimal("0.000001"))
        _require(abs(number - rounded) <= Decimal("0.000000001"))
    except (InvalidOperation, ValueError, OverflowError):
        raise QuoteUnavailable("Unsupported native monetary precision") from None
    return rounded


def _money(value):
    return format(_decimal(value), ".6f").rstrip("0").rstrip(".") or "0"


def _read(doctype, name):
    try:
        document = frappe.get_doc(doctype, _reference(name))
        document.check_permission("read")
    except (frappe.PermissionError, frappe.DoesNotExistError):
        raise QuoteUnavailable("Native read-only quote unavailable; manual review required") from None
    return document


def _stamp(document, fields):
    return {
        "doctype": document.doctype,
        "name": document.name,
        "modified": str(document.modified),
        **{field: document.get(field) for field in fields},
    }


def _inputs(proposal, context):
    _require(type(proposal) is dict and type(context) is dict)
    _require(set(context) == {"company", "pos_profile", "selling_price_list", "profile_modified", "currency"})
    for value in context.values():
        _reference(value)
    required = {"service_type", "customer", "phone", "promised_at", "items"}
    _require(required <= set(proposal) <= required | {"address"})
    _require(isinstance(proposal["service_type"], str) and proposal["service_type"] in {"Pickup", "Delivery"})
    _reference(proposal["customer"])
    phone = proposal["phone"]
    _require(isinstance(phone, str) and len(phone) <= 16)
    digits = phone[1:] if phone.startswith("+") else phone
    _require(digits.isascii() and digits.isdigit() and 7 <= len(digits) <= 15)
    try:
        _require(isinstance(proposal["promised_at"], str) and len(proposal["promised_at"]) <= 40)
        promised = datetime.fromisoformat(proposal["promised_at"].replace("Z", "+00:00"))
        _require(promised.tzinfo is not None and promised > datetime.now(timezone.utc))
    except (ValueError, TypeError):
        raise QuoteUnavailable("Unsupported native quote time") from None
    if proposal["service_type"] == "Delivery":
        _reference(proposal.get("address"))
    else:
        _require(not proposal.get("address"))
    rows = proposal["items"]
    _require(type(rows) is list and 1 <= len(rows) <= 50)
    seen = set()
    for row in rows:
        _require(type(row) is dict and {"item_code", "qty"} <= set(row) <= {"item_code", "qty", "note"})
        _reference(row["item_code"])
        _require(row["item_code"] not in seen)
        seen.add(row["item_code"])
        _require(type(row["qty"]) is int and 1 <= row["qty"] <= 1000)
        _require(isinstance(row.get("note", ""), str) and len(row.get("note", "")) <= 500)
    _require(len(json.dumps(proposal, ensure_ascii=True)) <= 16384)


def _context(proposal, context, evidence):
    actor = frappe.session.user
    _require(actor and actor != "Guest")
    user = frappe.db.get_value("User", actor, ["enabled", "user_type"], as_dict=True)
    _require(user and cint(user.enabled) and user.user_type == "System User")
    _require(get_user_restaurant_company() == context["company"])
    company = _read("Company", context["company"])
    regional = frappe.get_hooks("regional_overrides", {}).get(company.get("country"), {})
    _require(not any(path.startswith("erpnext.controllers.taxes_and_totals.") for path in regional))
    profile = _read("POS Profile", context["pos_profile"])
    _require(not cint(profile.get("disabled")) and profile.company == company.name)
    _require(str(profile.modified) == context["profile_modified"])
    _require(profile.selling_price_list == context["selling_price_list"])
    users = profile.get("applicable_for_users") or []
    _require(not users or actor in {row.user for row in users})
    _require(not profile.get("tax_category"))
    price_list = _read("Price List", context["selling_price_list"])
    _require(cint(price_list.get("enabled")) and cint(price_list.get("selling")))
    _require(company.default_currency == profile.currency == price_list.currency == context["currency"])
    settings = get_restaurant_settings(company=company.name, pos_profile=profile.name)
    try:
        settings.check_permission("read")
    except frappe.PermissionError:
        raise QuoteUnavailable("Native read-only quote unavailable; manual review required") from None
    _require(settings.company == company.name and settings.pos_profile == profile.name)
    _require(cint(settings.get("enable_delivery" if proposal["service_type"] == "Delivery" else "enable_pickup")))
    customer = _read("Customer", proposal["customer"])
    _require(not any(customer.get(f) for f in ("disabled", "is_internal_customer", "tax_category", "tax_withholding_category")))
    groups = profile.get("customer_groups") or []
    _require(not groups or customer.customer_group in {row.customer_group for row in groups})
    if proposal["service_type"] == "Delivery":
        address = _read("Address", proposal["address"])
        _require(not address.get("disabled") and not address.get("tax_category"))
        _require(any(row.link_doctype == "Customer" and row.link_name == customer.name for row in address.get("links") or []))
        evidence.append(_stamp(address, ("disabled", "tax_category")))
    # These reads are denial checks, not permission-free disclosure of rule data.
    _require(not frappe.db.exists("Pricing Rule", {"disable": 0, "selling": 1}))
    _require(not frappe.db.exists("Tax Rule", {"tax_type": "Sales"}))
    evidence.extend([
        _stamp(company, ("default_currency",)),
        _stamp(profile, ("currency", "selling_price_list", "taxes_and_charges", "posa_tax_inclusive", "disable_rounded_total")),
        _stamp(settings, ("enable_delivery", "enable_pickup", "delivery_fee_item")),
        _stamp(price_list, ("currency", "enabled", "selling", "price_not_uom_dependent")),
        _stamp(customer, ("disabled", "customer_group")),
    ])
    return profile, price_list, settings


def _item(code, profile, evidence, fee=False):
    item = _read("Item", code)
    _require(cint(item.get("is_sales_item")) and item.get("stock_uom"))
    _require(not any(item.get(f) for f in ("disabled", "has_serial_no", "has_batch_no", "has_variants", "variant_of", "is_fixed_asset", "is_customer_provided_item", "taxes")))
    _require(not fee or not cint(item.get("is_stock_item")))
    _require(not frappe.db.exists("Product Bundle", {"new_item_code": code}))
    allowed = profile.get("item_groups") or []
    _require(not allowed or item.item_group in {row.item_group for row in allowed})
    group, seen = item.get("item_group"), set()
    while group:
        _require(group not in seen and len(seen) < 20)
        seen.add(group)
        document = _read("Item Group", group)
        _require(not document.get("taxes"))
        evidence.append(_stamp(document, ("parent_item_group",)))
        group = document.get("parent_item_group")
    evidence.append(_stamp(item, ("stock_uom", "is_sales_item", "is_stock_item", "item_group")))
    return item


def _price(item, qty, customer, price_list, date, evidence):
    _require(frappe.has_permission("Item Price", "read"))
    # Limit before native priority/fallback selection: any ambiguity goes to handoff.
    candidates = frappe.get_all(
        "Item Price", filters={"item_code": item.name, "price_list": price_list.name},
        fields=["name"], limit_page_length=101,
    )
    _require(len(candidates) <= 100)
    applicable = []
    for row in candidates:
        price = _read("Item Price", row.name)
        if price.get("customer") not in (None, "", customer) or price.get("supplier") or price.get("batch_no"):
            continue
        if price.get("valid_from") and getdate(price.valid_from) > getdate(date):
            continue
        if price.get("valid_upto") and getdate(price.valid_upto) < getdate(date):
            continue
        if price.get("uom") not in (None, "", item.stock_uom):
            continue
        applicable.append(price)
    _require(len(applicable) == 1)
    price = applicable[0]
    _require(price.currency == price_list.currency and price.uom == item.stock_uom)
    _require(cint(price.get("selling")) and not price.get("buying"))
    packing = _decimal(price.get("packing_unit") or 0)
    _require(not packing or Decimal(qty) % packing == 0)
    expected = _decimal(price.price_list_rate, Decimal("1000000"))
    _require(expected > 0)
    native = get_price_list_rate_for(frappe._dict(
        price_list=price_list.name, customer=customer, uom=item.stock_uom,
        stock_uom=item.stock_uom, qty=qty, transaction_date=date,
        conversion_factor=1, ignore_party=False,
    ), item.name)
    _require(_decimal(native, Decimal("1000000")) == expected)
    evidence.append(_stamp(price, ("price_list_rate", "currency", "uom", "customer", "valid_from", "valid_upto", "packing_unit")))
    return float(expected)


def _taxes(profile, evidence):
    template = _read("Sales Taxes and Charges Template", profile.get("taxes_and_charges"))
    _require(template.company == profile.company and not cint(template.get("disabled")))
    rows = template.get("taxes") or []
    _require(1 <= len(rows) <= 10)
    result, seen = [], set()
    for row in rows:
        _require(row.charge_type == "On Net Total" and row.account_head not in seen)
        seen.add(row.account_head)
        _require(row.get("add_deduct_tax") in (None, "", "Add"))
        _require(not row.get("dont_recompute_tax"))
        rate = _decimal(row.rate, Decimal("100"))
        account = _read("Account", row.account_head)
        _require(account.company == profile.company and not account.get("is_group") and not account.get("disabled"))
        # A configured service charge need not be classified as a tax account.
        charge_account = (
            account.get("root_type") in {"Income", "Expense"}
            and account.get("report_type") == "Profit and Loss"
            and account.get("account_type") in {
                None, "", "Chargeable", "Income Account", "Expense Account",
                "Direct Income", "Indirect Income", "Direct Expense", "Indirect Expense",
            }
        )
        _require(account.account_type == "Tax" or charge_account)
        evidence.append(_stamp(account, ("company", "account_type", "root_type", "report_type", "is_group", "disabled")))
        result.append({
            "charge_type": "On Net Total", "account_head": account.name,
            "description": account.name, "rate": float(rate),
            "included_in_print_rate": cint(profile.get("posa_tax_inclusive")),
        })
    evidence.append(_stamp(template, ("company", "disabled")))
    evidence.append({"tax_rows": result})
    return result


def _calculate(values):
    # Construct only. Never run POS defaults, validate, document hooks or persistence.
    invoice = POSInvoice(values)
    keys = ("round_off_applicable_accounts", "round_row_wise_tax")
    flags = frappe.flags
    previous = {key: flags[key] for key in keys if key in flags}
    try:
        calculate_taxes_and_totals(invoice)
    finally:
        for key in keys:
            if key in previous:
                flags[key] = previous[key]
            else:
                flags.pop(key, None)
    _require(not invoice.get("rounding_adjustment"))
    return invoice


def quote_order(proposal, context):
    """Quote a normalized cart using current readable native data, or fail closed.

    All monetary outputs are transaction-currency decimal strings. Lines exclude
    the fee, while grand total includes it; inclusive charges are already in amounts.
    The tax field is native total_taxes_and_charges, not a tax-only breakdown.
    Same-currency only; unsupported pricing is never treated as a free cart.
    """
    _inputs(proposal, context)
    evidence = []
    profile, price_list, settings = _context(proposal, context, evidence)
    date, items = today(), []
    fee_code = settings.get("delivery_fee_item")
    for row in proposal["items"]:
        _require(row["item_code"] != fee_code)
        item = _item(row["item_code"], profile, evidence)
        rate = _price(item, row["qty"], proposal["customer"], price_list, date, evidence)
        items.append({"item_code": item.name, "qty": row["qty"], "rate": rate,
                      "price_list_rate": rate, "uom": item.stock_uom,
                      "stock_uom": item.stock_uom, "conversion_factor": 1,
                      "item_tax_template": None, "item_tax_rate": "{}",
                      "discount_percentage": 0, "discount_amount": 0,
                      "margin_rate_or_amount": 0, "total_weight": 0})
    delivery = proposal["service_type"] == "Delivery"
    if delivery:
        fee = _item(_reference(fee_code), profile, evidence, fee=True)
        rate = _price(fee, 1, proposal["customer"], price_list, date, evidence)
        items.append({**items[0], "item_code": fee.name, "qty": 1, "rate": rate,
                      "price_list_rate": rate, "uom": fee.stock_uom, "stock_uom": fee.stock_uom})
    invoice = _calculate({
        "doctype": "POS Invoice", "company": context["company"], "is_pos": 1,
        "pos_profile": profile.name, "customer": proposal["customer"],
        "currency": context["currency"], "conversion_rate": 1,
        "selling_price_list": price_list.name, "price_list_currency": context["currency"],
        "plc_conversion_rate": 1, "posting_date": date, "items": items,
        "taxes": _taxes(profile, evidence), "payments": [], "update_stock": 0,
        "disable_rounded_total": cint(profile.get("disable_rounded_total")),
        "discount_amount": 0, "additional_discount_percentage": 0,
    })
    _require(len(invoice.items) == len(items))
    for original, calculated in zip(items, invoice.items):
        _require(calculated.item_code == original["item_code"] and not isinstance(calculated.qty, bool)
                 and calculated.qty == original["qty"])
        _require(_decimal(calculated.rate) == _decimal(original["rate"]))
    result = {
        "currency": context["currency"],
        "lines": [{"item_code": row.item_code, "qty": int(row.qty),
                   "rate": _money(row.rate), "amount": _money(row.amount)}
                  for row in invoice.items[:len(proposal["items"])]],
        "tax": _money(invoice.total_taxes_and_charges),
        "total": _money(invoice.grand_total),
        "delivery_fee": _money(invoice.items[-1].amount) if delivery else "0",
    }
    _require(_decimal(result["total"]) > 0)
    fingerprint = {"version": 1, "proposal": proposal,
                   "context": context, "date": date, "evidence": evidence, "result": result,
                   "round_row_wise_tax": frappe.db.get_single_value("Accounts Settings", "round_row_wise_tax")}
    result["native_fingerprint"] = hashlib.sha256(
        json.dumps(fingerprint, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()
    return result
