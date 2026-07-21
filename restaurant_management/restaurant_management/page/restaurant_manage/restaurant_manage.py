from __future__ import unicode_literals
import frappe
from frappe import _
from erpnext.selling.page.point_of_sale.point_of_sale import get_items as get_v15_pos_items
from erpnext.stock.get_item_details import get_pos_profile

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

        if frappe.session.user == "Administrator" or user_perm.get("write") or user_perm.get("create"):
            rooms = frappe.get_all("Restaurant Object", "name, description", {
                "type": "Room",
            })
        else:
            restaurant_settings = frappe.get_single("Restaurant Settings")
            rooms_enabled = restaurant_settings.rooms_access()

            rooms = frappe.get_all("Restaurant Object", "name, description", {
                "type": "Room",
                "name": ("in", rooms_enabled)
            })

        for room in rooms:
            t = frappe.get_doc("Restaurant Object", room.name)
            room["orders_count"] = t.orders_count

        return rooms

    @staticmethod
    def add_room():
        room = frappe.new_doc("Restaurant Object")
        room.type = "Room"
        room.description = f"Room {(RestaurantManage().count_roms() + 1)}"
        room.save()

        return room

    @staticmethod
    def count_roms():
        return frappe.db.count("Restaurant Object", filters={"type": "Room"})

    @staticmethod
    def listener(data):
        for d in data:
            if len(data[d]["data"]) == 0:
                return data

            if d == "Table":
                cond = "and `table` in (%s)" % (', '.join([f"'{row}'" for row in data[d]["data"]]))

                oc = frappe.db.sql(f"""
                        SELECT `table` as name, count(`table`) as count
                        FROM `tabTable Order`
                        WHERE status = 'Attending' {cond}
                        GROUP by `table`
                        """, as_dict=True)

                for o in oc:
                    data[d]["data"][o.name]["count"] = o.count

            if d == "Room":
                cond = "and `room` in (%s)" % (', '.join([f"'{row}'" for row in data[d]["data"]]))

                oc = frappe.db.sql(f"""
                        SELECT `room` as name, count(`room`) as count
                        FROM `tabTable Order`
                        WHERE status = 'Attending' {cond}
                        GROUP by `room`
                        """, as_dict=True)

                for o in oc:
                    data[d]["data"][o.name]["count"] = o.count

            if d == "Production Center":
                for pc in data[d]["data"]:
                    production_center = frappe.get_doc("Restaurant Object", pc)

                    data[d]["data"][pc]["count"] = production_center.orders_count_in_production_center

            if d == "Process":
                production_center = frappe.get_doc("Restaurant Object", data[d]["data"])
                status_managed = production_center.status_managed

                filters = {
                    "status": ("in", [item.status_managed for item in status_managed]),
                    "item_group": ("in", production_center._items_group),
                    "parent": ("!=", "")
                }

                data = dict(Process=frappe.get_all("Order Entry Item", "identifier,status", filters=filters))

        return data


@frappe.whitelist()
def get_bootstrap():
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)

    company = frappe.defaults.get_user_default("company")
    if not company:
        frappe.throw(_("Set a default Company before opening Restaurant Manage"))

    if not frappe.has_permission("Company", "read", company):
        frappe.throw(_("Not permitted to use Company {0}").format(company), frappe.PermissionError)

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
    restaurant_settings = frappe.get_single("Restaurant Settings")
    return restaurant_settings.settings_data()


def pos_profile_data():
    restaurant_settings = frappe.get_single("Restaurant Settings")
    return restaurant_settings.pos_profile_data()

def set_settings_data(doc, method=None):
    frappe.publish_realtime("update_settings")

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
