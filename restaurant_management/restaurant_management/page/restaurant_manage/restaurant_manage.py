from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.selling.page.point_of_sale.point_of_sale import get_items as get_v15_pos_items
from erpnext.stock.get_item_details import get_pos_profile
from restaurant_management.restaurant_management.company_settings import (
    get_user_restaurant_company,
    get_restaurant_settings,
)

def get_active_restaurant_company():
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)
    company = get_user_restaurant_company()
    if not company:
        frappe.throw(_("Set a default Company before opening Restaurant Manage"))
    if not frappe.has_permission("Company", "read", company):
        frappe.throw(
            _("Not permitted to use Company {0}").format(company),
            frappe.PermissionError,
        )
    return company

class RestaurantManage:
    @staticmethod
    def production_center_notify(status):
        object_in_status = frappe.get_all("Status Managed Production Center", pluck="parent", filters={
            "parenttype": "Restaurant Object",
            "status_managed": ("in", status)
        })

        for center_name in set(object_in_status):
            obj = frappe.get_doc("Restaurant Object", center_name)
            obj.synchronize()

    @staticmethod
    def get_rooms():
        user_perm = frappe.permissions.get_doc_permissions(
            frappe.new_doc("Restaurant Object"))

        company = get_active_restaurant_company()
        if frappe.session.user == "Administrator" or user_perm.get("write") or user_perm.get("create"):
            rooms = frappe.get_all("Restaurant Object", "name, description", {
                "type": "Room",
                "company": company,
            })
        else:
            settings = get_restaurant_settings(company=company)
            rooms_enabled = settings.rooms_access()

            rooms = frappe.get_all("Restaurant Object", "name, description", {
                "type": "Room",
                "name": ("in", rooms_enabled),
                "company": company,
            })

        for room in rooms:
            t = frappe.get_doc("Restaurant Object", room.name)
            room["orders_count"] = t.orders_count

        return rooms

    @staticmethod
    def add_room():
        room = frappe.new_doc("Restaurant Object")
        room.type = "Room"
        room.company = get_active_restaurant_company()
        room.description = f"Room {(RestaurantManage().count_roms() + 1)}"
        room.save()

        return room

    @staticmethod
    def count_roms():
        return frappe.db.count("Restaurant Object", filters={
            "type": "Room",
            "company": get_active_restaurant_company(),
        })

    @staticmethod
    def listener(data):
        company = get_active_restaurant_company()
        for object_type in data:
            payload = data[object_type]["data"]
            if not payload:
                continue

            if object_type in {"Table", "Room"}:
                fieldname = object_type.lower()
                names = list(payload)
                counts = frappe.get_all(
                    "Table Order",
                    filters={
                        fieldname: ("in", names),
                        "status": "Attending",
                        "company": company,
                    },
                    fields=[
                        f"{fieldname} as name",
                        "count(name) as count",
                    ],
                    group_by=fieldname,
                )
                for row in counts:
                    if row.name in payload:
                        payload[row.name]["count"] = row.count

            elif object_type == "Production Center":
                for center_name in list(payload):
                    center = frappe.get_doc("Restaurant Object", center_name)
                    if center.company != company:
                        payload.pop(center_name, None)
                        continue
                    payload[center_name]["count"] = center.orders_count_in_production_center

            elif object_type == "Process":
                center = frappe.get_doc("Restaurant Object", payload)
                if center.company != company:
                    frappe.throw(_("Production Center belongs to another company"))
                order_names = frappe.get_all(
                    "Table Order",
                    filters={"company": company},
                    pluck="name",
                    limit_page_length=0,
                )
                filters = {
                    "status": ("in", center._status_managed),
                    "item_group": ("in", center._items_group),
                    "parent": ("in", order_names or [""]),
                }
                data = dict(Process=frappe.get_all(
                    "Order Entry Item",
                    "identifier,status",
                    filters=filters,
                ))

        return data


@frappe.whitelist()
def get_bootstrap():
    company = get_active_restaurant_company()

    pos_profile = get_pos_profile(company, user=frappe.session.user)
    if not pos_profile or pos_profile.get("disabled"):
        frappe.throw(
            _("No enabled POS Profile is available for {0}").format(company)
        )

    installed_apps = set(frappe.get_installed_apps())
    return {
        "company": company,
        "pos_profile": pos_profile.name,
        "capabilities": {
            "electronic_invoicing": "ovenube_peru" in installed_apps,
            "silent_print": "silent_print" in installed_apps,
            "hardware_bridge": "silent_print" in installed_apps,
        },
    }



@frappe.whitelist()
def get_rooms():
    return RestaurantManage().get_rooms()


@frappe.whitelist()
def add_room(client=None):
    room = RestaurantManage().add_room()
    response = dict(
        company=room.company,
        client=client,
        current_room=room.name,
        rooms=RestaurantManage().get_rooms()
    )
    frappe.publish_realtime("check_rooms", response, after_commit=True)
    return response


@frappe.whitelist(allow_guest=True)
def get_work_station():
    work_stations = frappe.get_all("Work Station")
    work_station = frappe.get_doc("Work Station", work_stations[0].name)
    return {
        "work_station": work_station,
        "pos_profile": frappe.get_doc("POS Profile", work_station.pos_profile)
    }


@frappe.whitelist()
def listeners(args):
    import json
    return RestaurantManage().listener(json.loads(args))


@frappe.whitelist()
def get_settings_data():
    settings = get_restaurant_settings(company=get_active_restaurant_company())
    return settings.settings_data()


@frappe.whitelist()
def get_restaurant_opening_entry(pos_profile):
    """Return the active opening for the restaurant POS Profile.

    Restaurant orders are shared by the users assigned to the same POS Profile,
    while ERPNext's standard POS endpoint only looks for an opening owned by the
    current user. Waiters must therefore reuse the cashier's active opening
    instead of being prompted to create a second cash session.
    """
    company = get_active_restaurant_company()
    assigned_profile = get_pos_profile(company, user=frappe.session.user)
    if not assigned_profile or assigned_profile.name != pos_profile:
        frappe.throw(
            _("POS Profile {0} is not assigned to the current user").format(
                pos_profile
            ),
            frappe.PermissionError,
        )

    openings = frappe.get_all(
        "POS Opening Entry",
        filters={
            "company": company,
            "pos_profile": pos_profile,
            "status": "Open",
            "docstatus": 1,
        },
        fields=[
            "name",
            "company",
            "pos_profile",
            "period_start_date",
            "user",
        ],
        order_by="period_start_date desc",
        limit_page_length=20,
    )
    own_opening = next(
        (opening for opening in openings if opening.user == frappe.session.user),
        None,
    )
    opening = own_opening or (openings[0] if openings else None)
    can_manage_opening = bool(
        {"System Manager", "Accounts Manager", "resto_admin", "resto_cajero"}
        & set(frappe.get_roles())
    )

    return {
        "allow_negative_stock": frappe.db.get_single_value(
            "Stock Settings", "allow_negative_stock"
        ),
        "opening": opening,
        "can_manage_opening": can_manage_opening,
        "owns_opening": bool(
            opening and opening.user == frappe.session.user
        ),
    }


def pos_profile_data():
    settings = get_restaurant_settings()
    return settings.pos_profile_data()

def set_settings_data(doc, method=None):
    company = doc.get("company") or frappe.db.get_value(
        "POS Profile", doc.get("parent"), "company"
    )
    frappe.publish_realtime("update_settings", {"company": company}, after_commit=True)

def set_pos_profile(doc, method=None):
    frappe.publish_realtime("pos_profile_update", pos_profile_data())


def notify_to_check_command(command_foods):
    frappe.publish_realtime("notify_to_check_order_data", dict(
        commands_foods=command_foods
    ))


def debug_data(data):
    frappe.publish_realtime("debug_data", data)


@frappe.whitelist()
def get_items(start, page_length, price_list, pos_profile, item_group=None, search_value=""):
    """Adapt the legacy restaurant item request to the ERPNext v15 POS contract."""
    root_item_group = _get_pos_item_group_root(pos_profile)
    item_group = _get_permitted_item_group(item_group, root_item_group)
    result = get_v15_pos_items(
        start=start,
        page_length=page_length,
        price_list=price_list,
        item_group=item_group,
        pos_profile=pos_profile,
        search_term=search_value,
    )

    if isinstance(result, list):
        return {"items": result}

    return result or {"items": []}


@frappe.whitelist()
def get_item_group_root(pos_profile):
    return _get_pos_item_group_root(pos_profile)


def _get_pos_item_group_root(pos_profile):
    configured_groups = frappe.get_all(
        "POS Item Group",
        filters={"parent": pos_profile},
        pluck="item_group",
    )

    if configured_groups:
        group_bounds = frappe.get_all(
            "Item Group",
            filters={"name": ("in", configured_groups)},
            fields=["lft", "rgt"],
        )
        if group_bounds:
            minimum_lft = min(group.lft for group in group_bounds)
            maximum_rgt = max(group.rgt for group in group_bounds)
            ancestors = frappe.get_all(
                "Item Group",
                filters={
                    "is_group": 1,
                    "lft": ("<=", minimum_lft),
                    "rgt": (">=", maximum_rgt),
                },
                fields=["name"],
                order_by="lft desc",
                limit_page_length=1,
            )
            if ancestors:
                return ancestors[0].name

    roots = frappe.get_all(
        "Item Group",
        filters={"is_group": 1},
        fields=["name"],
        order_by="rgt desc",
        limit_page_length=1,
    )
    if not roots:
        frappe.throw(_("Configure at least one Item Group before using Restaurant Manage"))

    return roots[0].name


def _get_permitted_item_group(item_group, root_item_group):
    if not item_group:
        return root_item_group

    bounds = frappe.db.get_value(
        "Item Group",
        item_group,
        ["lft", "rgt"],
        as_dict=True,
    )
    root_bounds = frappe.db.get_value(
        "Item Group",
        root_item_group,
        ["lft", "rgt"],
        as_dict=True,
    )
    if not bounds or not root_bounds:
        return root_item_group

    is_within_root = bounds.lft >= root_bounds.lft and bounds.rgt <= root_bounds.rgt
    return item_group if is_within_root else root_item_group
