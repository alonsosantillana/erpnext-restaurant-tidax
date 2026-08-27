from __future__ import unicode_literals

import re

import frappe
from frappe import _
from frappe.model.naming import NamingSeries, make_autoname
from frappe.utils import cstr

from restaurant_management.restaurant_management.company_settings import (
    COMPANY_SETTINGS_DOCTYPE,
    get_user_restaurant_company,
    get_restaurant_settings,
)


POS_SERIES_FIELDS = {
    "POS Opening Entry": "pos_opening_series",
    "POS Closing Entry": "pos_closing_series",
}
POS_SERIES_PREFIXES = {
    "POS Opening Entry": "POS-OPE",
    "POS Closing Entry": "POS-CLO",
}
SERIES_DISPLAY_FIELD = "restaurant_naming_series"
TABLE_ORDER_SERIES_FIELD = "order_naming_series"


def get_company_series_abbreviation(company):
    abbr = cstr(frappe.db.get_value("Company", company, "abbr")).strip().upper()
    abbr = re.sub(r"[^A-Z0-9-]+", "-", abbr).strip("-")
    if not abbr:
        frappe.throw(_("Company {0} requires an abbreviation").format(company))
    return abbr


def get_default_pos_series(company, document_type):
    if document_type not in POS_SERIES_FIELDS:
        frappe.throw(_("Unsupported POS series document: {0}").format(document_type))

    abbr = get_company_series_abbreviation(company)

    return f"{POS_SERIES_PREFIXES[document_type]}-{abbr}-.YYYY.-.#####"


def get_default_table_order_series(company):
    return f"OR-{get_company_series_abbreviation(company)}-.YYYY.-.#####"


def validate_company_pos_series(settings):
    if settings.doctype != COMPANY_SETTINGS_DOCTYPE:
        return

    configured = {}
    order_series = cstr(settings.get(TABLE_ORDER_SERIES_FIELD)).strip()
    if not order_series:
        order_series = get_default_table_order_series(settings.company)
        settings.set(TABLE_ORDER_SERIES_FIELD, order_series)
    NamingSeries(order_series).validate()
    configured[TABLE_ORDER_SERIES_FIELD] = order_series

    for document_type, fieldname in POS_SERIES_FIELDS.items():
        series = cstr(settings.get(fieldname)).strip()
        if not series:
            series = get_default_pos_series(settings.company, document_type)
            settings.set(fieldname, series)

        NamingSeries(series).validate()
        settings.set(fieldname, series)
        configured[fieldname] = series

    if len(set(configured.values())) != len(configured):
        frappe.throw(_("Restaurant document series must be different"))

    for series in configured.values():
        for other_fieldname in [TABLE_ORDER_SERIES_FIELD, *POS_SERIES_FIELDS.values()]:
            company = frappe.db.get_value(
                COMPANY_SETTINGS_DOCTYPE,
                {
                    "name": ("!=", settings.name),
                    other_fieldname: series,
                },
                "company",
            )
            if company:
                frappe.throw(
                    _("Restaurant series {0} is already assigned to company {1}").format(
                        series, company
                    )
                )


def get_company_table_order_series(company):
    settings = get_restaurant_settings(company=company)
    series = cstr(settings.get(TABLE_ORDER_SERIES_FIELD)).strip()
    if not series:
        series = get_default_table_order_series(company)
    NamingSeries(series).validate()
    return series


def resolve_table_order_company(doc):
    if doc.doctype != "Table Order":
        frappe.throw(_("Unsupported restaurant order document: {0}").format(doc.doctype))

    company = doc.get("company")
    profile = doc.get("pos_profile")
    table = doc.get("table")
    profile_company = (
        frappe.db.get_value("POS Profile", profile, "company") if profile else None
    )
    table_company = (
        frappe.db.get_value("Restaurant Object", table, "company") if table else None
    )

    companies = {value for value in (company, profile_company, table_company) if value}
    if len(companies) > 1:
        frappe.throw(_("Table Order context belongs to different companies"))

    company = next(iter(companies), None) or get_user_restaurant_company()
    if not company:
        frappe.throw(_("Company is required to resolve the Table Order series"))
    doc.company = company
    return company


def autoname_table_order(doc, method=None):
    company = resolve_table_order_company(doc)
    series = get_company_table_order_series(company)
    doc.naming_series = series
    doc.name = make_autoname(series, doc=doc)


def get_company_pos_series(company, document_type):
    fieldname = POS_SERIES_FIELDS.get(document_type)
    if not fieldname:
        frappe.throw(_("Unsupported POS series document: {0}").format(document_type))

    settings = get_restaurant_settings(company=company)
    series = cstr(settings.get(fieldname)).strip()
    if not series:
        frappe.throw(
            _("Configure {0} in Restaurant Company Settings for {1}").format(
                settings.meta.get_label(fieldname), company
            )
        )

    NamingSeries(series).validate()
    return series


def resolve_pos_document_company(doc):
    if doc.doctype not in POS_SERIES_FIELDS:
        frappe.throw(_("Unsupported POS series document: {0}").format(doc.doctype))

    company = doc.get("company")
    profile = doc.get("pos_profile")

    if doc.doctype == "POS Closing Entry" and doc.get("pos_opening_entry"):
        opening = frappe.db.get_value(
            "POS Opening Entry",
            doc.pos_opening_entry,
            ["company", "pos_profile"],
            as_dict=True,
        )
        if not opening:
            frappe.throw(
                _("POS Opening Entry {0} does not exist").format(
                    doc.pos_opening_entry
                )
            )
        if company and company != opening.company:
            frappe.throw(
                _("POS Closing Entry and POS Opening Entry belong to different companies")
            )
        if profile and profile != opening.pos_profile:
            frappe.throw(
                _("POS Closing Entry and POS Opening Entry use different POS Profiles")
            )
        company = company or opening.company
        profile = profile or opening.pos_profile
        doc.company = company
        doc.pos_profile = profile

    if profile:
        profile_company = frappe.db.get_value("POS Profile", profile, "company")
        if not profile_company:
            frappe.throw(_("POS Profile {0} does not exist").format(profile))
        if company and company != profile_company:
            frappe.throw(
                _("POS Profile {0} does not belong to company {1}").format(
                    profile, company
                )
            )
        company = company or profile_company
        doc.company = company

    if not company:
        frappe.throw(_("Company is required to resolve the POS series"))

    return company


def autoname_pos_document(doc, method=None):
    company = resolve_pos_document_company(doc)
    series = get_company_pos_series(company, doc.doctype)
    doc.set(SERIES_DISPLAY_FIELD, series)
    doc.name = make_autoname(series, doc=doc)


def validate_pos_document_series(doc, method=None):
    company = resolve_pos_document_company(doc)
    expected = get_company_pos_series(company, doc.doctype)
    provided = cstr(doc.get(SERIES_DISPLAY_FIELD)).strip()
    if provided and provided != expected:
        frappe.throw(
            _("The POS series does not belong to company {0}").format(company),
            frappe.PermissionError,
        )
    doc.set(SERIES_DISPLAY_FIELD, expected)


@frappe.whitelist()
def get_pos_document_series(company, document_type):
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)
    if not frappe.has_permission("Company", "read", company):
        frappe.throw(
            _("Not permitted to use Company {0}").format(company),
            frappe.PermissionError,
        )
    return get_company_pos_series(company, document_type)
