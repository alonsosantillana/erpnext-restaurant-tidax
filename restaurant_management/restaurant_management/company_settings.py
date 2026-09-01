from __future__ import unicode_literals

import frappe
from frappe import _
from erpnext.stock.get_item_details import get_pos_profile


COMPANY_SETTINGS_DOCTYPE = "Restaurant Company Settings"
LEGACY_SETTINGS_DOCTYPE = "Restaurant Settings"


def get_user_restaurant_company(user=None):
    """Return the active Company or the user's default Company permission."""
    user = user or frappe.session.user
    company = frappe.defaults.get_user_default("company", user=user)
    if company:
        return company

    if not user or user == "Guest":
        return None

    return frappe.db.get_value(
        "User Permission",
        {
            "user": user,
            "allow": "Company",
            "is_default": 1,
            "apply_to_all_doctypes": 1,
        },
        "for_value",
    )


def _document_company(document, doctype):
    if not document:
        return None
    if isinstance(document, str):
        return frappe.db.get_value(doctype, document, "company")
    return document.get("company") if hasattr(document, "get") else None


def resolve_restaurant_company(
    company=None,
    pos_profile=None,
    order=None,
    fulfillment=None,
):
    """Resolve the company from the most authoritative restaurant context."""
    order_company = _document_company(order, "Table Order")
    fulfillment_company = _document_company(
        fulfillment, "Restaurant Fulfillment"
    )
    profile_company = (
        frappe.db.get_value("POS Profile", pos_profile, "company")
        if pos_profile
        else None
    )

    document_companies = {
        value for value in (order_company, fulfillment_company) if value
    }
    if len(document_companies) > 1:
        frappe.throw(_("Restaurant documents belong to different companies"))

    resolved = next(iter(document_companies), None)
    if resolved and profile_company and resolved != profile_company:
        frappe.throw(_("The POS Profile does not belong to order company {0}").format(resolved))
    if resolved and company and resolved != company:
        frappe.throw(_("The requested company does not match order company {0}").format(resolved))
    if profile_company and company and profile_company != company:
        frappe.throw(_("The POS Profile does not belong to company {0}").format(company))

    return (
        resolved
        or profile_company
        or company
        or get_user_restaurant_company()
    )


def get_legacy_settings_company():
    if not frappe.db.exists("DocType", LEGACY_SETTINGS_DOCTYPE):
        return None
    return frappe.db.get_single_value(
        LEGACY_SETTINGS_DOCTYPE, "legacy_company"
    )


def get_restaurant_settings(
    company=None,
    pos_profile=None,
    order=None,
    fulfillment=None,
    required=True,
):
    company = resolve_restaurant_company(
        company=company,
        pos_profile=pos_profile,
        order=order,
        fulfillment=fulfillment,
    )
    if not company:
        if required:
            frappe.throw(_("Set a default Company before using Restaurant Management"))
        return None

    settings_name = frappe.db.get_value(
        COMPANY_SETTINGS_DOCTYPE,
        {"company": company},
        "name",
    )
    if settings_name:
        return frappe.get_doc(COMPANY_SETTINGS_DOCTYPE, settings_name)

    if required:
        frappe.throw(
            _("Configure Restaurant Company Settings for {0}").format(company)
        )
    return None


def get_restaurant_setting_value(
    fieldname,
    company=None,
    pos_profile=None,
    order=None,
    fulfillment=None,
    default=None,
    required=True,
):
    settings = get_restaurant_settings(
        company=company,
        pos_profile=pos_profile,
        order=order,
        fulfillment=fulfillment,
        required=required,
    )
    if not settings:
        return default
    value = settings.get(fieldname)
    return default if value is None else value


class RestaurantSettingsMixin:
    @property
    def settings_company(self):
        return self.get("company") or get_legacy_settings_company()

    def validate_restaurant_settings(self):
        company = self.settings_company
        if self.doctype == COMPANY_SETTINGS_DOCTYPE and not company:
            frappe.throw(_("Company is required"))
        if self.flags.get("restaurant_settings_migration"):
            return
        if self.doctype == LEGACY_SETTINGS_DOCTYPE and not company:
            return

        if self.doctype == COMPANY_SETTINGS_DOCTYPE:
            from restaurant_management.restaurant_management.pos_series import (
                validate_company_pos_series,
            )

            validate_company_pos_series(self)

        if self.get("pos_profile"):
            profile_company = frappe.db.get_value(
                "POS Profile", self.pos_profile, "company"
            )
            if profile_company != company:
                frappe.throw(
                    _("POS Profile {0} does not belong to company {1}").format(
                        self.pos_profile, company
                    )
                )

        if self.get("delivery_fee_item"):
            item = frappe.db.get_value(
                "Item",
                self.delivery_fee_item,
                ["disabled", "is_sales_item"],
                as_dict=True,
            )
            if not item or item.disabled or not item.is_sales_item:
                frappe.throw(
                    _("Delivery Fee Item must be an enabled sales Item")
                )

        if self.get("enable_tips"):
            self._validate_tip_payable_account(company)

    def _validate_tip_payable_account(self, company):
        account_name = self.get("tip_payable_account")
        if not account_name:
            frappe.throw(_("Configure the Tips Payable Account"))

        account = frappe.db.get_value(
            "Account",
            account_name,
            ["company", "root_type", "is_group", "disabled"],
            as_dict=True,
        )
        if not account or account.disabled:
            frappe.throw(_("Tips Payable Account must be an enabled Account"))
        if account.company != company:
            frappe.throw(
                _("Tips Payable Account must belong to company {0}").format(company)
            )
        if account.root_type != "Liability" or account.is_group:
            frappe.throw(
                _("Tips Payable Account must be a non-group Liability account")
            )

    def publish_settings_update(self):
        frappe.publish_realtime(
            "update_settings",
            {"company": self.settings_company},
            after_commit=True,
        )

    def settings_data(self):
        profile = frappe.db.get_value(
            "User", frappe.session.user, "role_profile_name"
        )
        return dict(
            company=self.settings_company,
            pos=self.pos_profile_data(),
            permissions=dict(
                invoice=frappe.permissions.get_doc_permissions(
                    frappe.new_doc("Sales Invoice")
                ),
                order=frappe.permissions.get_doc_permissions(
                    frappe.new_doc("Table Order")
                ),
                restaurant_object=frappe.permissions.get_doc_permissions(
                    frappe.new_doc("Restaurant Object")
                ),
                rooms_access=list(self.rooms_access()),
                configured_rooms_count=frappe.db.count(
                    "Restaurant Object",
                    {"type": "Room", "company": self.settings_company},
                ),
            ),
            restrictions=self,
            exceptions=[
                item
                for item in self.get("restaurant_exceptions", [])
                if item.role_profile == profile
            ],
            lang=frappe.session.data.lang,
            order_item_editor_form=self.get_order_item_editor_form(),
        )

    def pos_profile_data(self):
        pos_profile_name = self.get_current_pos_profile_name()
        return dict(
            has_pos=pos_profile_name is not None,
            pos=(
                frappe.get_doc("POS Profile", pos_profile_name)
                if pos_profile_name
                else None
            ),
        )

    def get_order_item_editor_form(self):
        return frappe.get_doc("Desk Form", "order-item-editor")

    def get_current_pos_profile_name(self):
        company = self.settings_company or frappe.defaults.get_user_default(
            "company"
        )
        profile = get_pos_profile(company, user=frappe.session.user)
        return profile.name if profile else None

    def rooms_access(self):
        pos_profile_name = self.get_current_pos_profile_name()
        if not pos_profile_name:
            return []

        permission_parent = frappe.db.get_value(
            "POS Profile User",
            filters={
                "parenttype": "POS Profile",
                "parent": pos_profile_name,
                "user": frappe.session.user,
            },
            fieldname="name",
        )
        if not permission_parent:
            return []

        return frappe.get_all(
            "Restaurant Permission",
            filters={
                "parenttype": "Restaurant Permission Manage",
                "parent": permission_parent,
            },
            pluck="room",
        )
