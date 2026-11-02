"""Opt-in v16 compatibility for a restaurant's permanent POS opening."""

import frappe
from frappe import _
from frappe.utils import cint, getdate, today, get_datetime, now_datetime

from restaurant_management.restaurant_management.company_settings import get_restaurant_settings


class PermanentPOSOpeningMixin:
    def validate_pos_opening_entry(self):
        if not self.pos_profile or not self.company:
            return super().validate_pos_opening_entry()

        settings = get_restaurant_settings(
            company=self.company, pos_profile=self.pos_profile, required=False
        )
        if (
            not settings
            or not cint(settings.get("allow_permanent_pos_opening"))
            or settings.get("company") != self.company
            or settings.get("pos_profile") != self.pos_profile
        ):
            return super().validate_pos_opening_entry()

        # Keep native cardinality: never filter out invalid entries or other users.
        openings = frappe.get_all(
            "POS Opening Entry",
            fields=["name", "period_start_date", "company", "docstatus"],
            filters={"pos_profile": self.pos_profile, "status": "Open"},
            order_by="period_start_date desc",
        )
        if len(openings) != 1:
            return super().validate_pos_opening_entry()

        opening = openings[0]
        if cint(opening.docstatus) != 1:
            frappe.throw(_("The active POS Opening Entry must be submitted."))
        if opening.company != self.company:
            frappe.throw(_("The active POS Opening Entry belongs to another company."))
        reference = self.get("restaurant_pos_opening_entry")
        if reference and reference != opening.name:
            frappe.throw(_("The POS Invoice refers to a different POS Opening Entry."))
        if not opening.period_start_date or get_datetime(opening.period_start_date) > now_datetime():
            frappe.throw(_("The active POS Opening Entry must have a valid non-future start date."))
        if getdate(opening.period_start_date) == getdate(today()):
            return super().validate_pos_opening_entry()
        # Only the same-day restriction is relaxed; no dates or documents change.
