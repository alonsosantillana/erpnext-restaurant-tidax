from urllib.parse import urlparse
import re

import frappe
from frappe import _
from frappe.model.document import Document


class PedidosYaIntegrationSettings(Document):
    def validate(self):
        self.remote_id = str(self.remote_id or "").strip()
        if not self.remote_id:
            frappe.throw(_("PedidosYa Remote ID is required"))
        if self.enabled and urlparse(self.api_base_url or "").scheme != "https":
            frappe.throw(_("PedidosYa API Base URL must use HTTPS"))

        profile_company = frappe.db.get_value("POS Profile", self.pos_profile, "company")
        if profile_company and profile_company != self.company:
            frappe.throw(_("The POS Profile must belong to the selected Company"))
        if self.integration_user and not frappe.db.get_value("User", self.integration_user, "enabled"):
            frappe.throw(_("The PedidosYa integration user must be enabled"))
        if self.default_customer and frappe.db.get_value("Customer", self.default_customer, "disabled"):
            frappe.throw(_("The default PedidosYa customer is disabled"))
        digits = re.sub(r"\D", "", str(self.fallback_contact_phone or ""))
        if len(digits) < 6 or len(digits) > 20:
            frappe.throw(_("Configure a valid fallback contact phone"))
        if self.default_payment_timing == "Cash on Delivery" and not self.expected_payment_method:
            frappe.throw(_("Configure an expected payment method for cash on delivery"))
        if self.enabled and (not self.api_username or not self.get_password("api_password")):
            frappe.throw(_("Configure PedidosYa API credentials before enabling the integration"))

        seen = set()
        for row in self.item_mappings:
            row.remote_code = str(row.remote_code or "").strip()
            if row.remote_code in seen:
                frappe.throw(_("Duplicate PedidosYa Remote Code: {0}").format(row.remote_code))
            seen.add(row.remote_code)
            item = frappe.db.get_value("Item", row.item_code, ["disabled", "is_sales_item"], as_dict=True)
            if not item or item.disabled or not item.is_sales_item:
                frappe.throw(_("Mapped Item {0} must be an enabled sales item").format(row.item_code))
