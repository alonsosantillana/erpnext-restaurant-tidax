# -*- coding: utf-8 -*-
# Copyright (c) 2022, Quantum Bit Core and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document


class RestaurantPermissionManage(Document):
    def on_update(self):
        frappe.publish_realtime("update_settings")


def _get_profile_user_context(pos_profile_user):
    profile_user = frappe.db.get_value(
        "POS Profile User",
        pos_profile_user,
        ["name", "user", "parent", "parenttype"],
        as_dict=True,
    )
    if not profile_user or profile_user.parenttype != "POS Profile":
        frappe.throw(
            _("POS Profile User {0} was not found").format(pos_profile_user)
        )

    profile = frappe.get_doc("POS Profile", profile_user.parent)
    profile.check_permission("write")
    return profile_user, profile


@frappe.whitelist()
def get_room_permissions(pos_profile_user):
    profile_user, profile = _get_profile_user_context(pos_profile_user)
    rooms = frappe.get_all(
        "Restaurant Object",
        filters={"type": "Room", "company": profile.company},
        fields=["name", "description"],
        order_by="description asc, name asc",
    )
    assigned_rooms = frappe.get_all(
        "Restaurant Permission",
        filters={
            "parent": profile_user.name,
            "parenttype": "Restaurant Permission Manage",
        },
        pluck="room",
    )
    return {
        "user": profile_user.user,
        "company": profile.company,
        "rooms": rooms,
        "assigned_rooms": assigned_rooms,
    }


@frappe.whitelist()
def save_room_permissions(pos_profile_user, rooms=None):
    profile_user, profile = _get_profile_user_context(pos_profile_user)
    selected_rooms = frappe.parse_json(rooms) if isinstance(rooms, str) else rooms
    if selected_rooms is None:
        selected_rooms = []
    if not isinstance(selected_rooms, list):
        frappe.throw(_("Rooms must be a list"))

    selected_rooms = list(dict.fromkeys(room for room in selected_rooms if room))
    allowed_rooms = set(
        frappe.get_all(
            "Restaurant Object",
            filters={"type": "Room", "company": profile.company},
            pluck="name",
        )
    )
    invalid_rooms = [room for room in selected_rooms if room not in allowed_rooms]
    if invalid_rooms:
        frappe.throw(
            _("Rooms do not belong to company {0}: {1}").format(
                profile.company, ", ".join(invalid_rooms)
            )
        )

    if frappe.db.exists("Restaurant Permission Manage", profile_user.name):
        permissions = frappe.get_doc(
            "Restaurant Permission Manage", profile_user.name
        )
    else:
        permissions = frappe.new_doc("Restaurant Permission Manage")
        permissions.pos_profile_user = profile_user.name

    permissions.set("restaurant_permission", [])
    for room in selected_rooms:
        permissions.append("restaurant_permission", {"room": room})

    permissions.flags.ignore_permissions = True
    if permissions.is_new():
        permissions.insert()
    else:
        permissions.save()

    return {"assigned_rooms": selected_rooms}
