from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.model.document import Document


class RestaurantMobileRequest(Document):
    def validate(self):
        if self.status not in {"Processing", "Completed"}:
            frappe.throw(_("Invalid mobile request status"))
        if self.status == "Completed":
            if not self.completed_on or not self.response_json:
                frappe.throw(_("A completed mobile request requires its result"))
            try:
                response = json.loads(self.response_json)
            except (TypeError, ValueError):
                frappe.throw(_("Mobile request response must be valid JSON"))
            if not isinstance(response, dict):
                frappe.throw(_("Mobile request response must be a JSON object"))
