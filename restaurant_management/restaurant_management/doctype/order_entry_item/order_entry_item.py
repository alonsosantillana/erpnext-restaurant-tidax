# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document


PREPARATION_TIME_FIELD = "custom_restaurant_preparation_time"


def preparation_targets(item_codes):
    item_codes = list(dict.fromkeys(code for code in item_codes if code))
    if not item_codes:
        return {}

    items = frappe.get_all(
        "Item",
        filters={"name": ("in", item_codes)},
        fields=["name", "item_group", PREPARATION_TIME_FIELD],
        limit_page_length=len(item_codes),
    )
    group_names = list(dict.fromkeys(item.item_group for item in items if item.item_group))
    group_targets = {
        row.name: frappe.utils.flt(row.get(PREPARATION_TIME_FIELD))
        for row in frappe.get_all(
            "Item Group",
            filters={"name": ("in", group_names)},
            fields=["name", PREPARATION_TIME_FIELD],
            limit_page_length=len(group_names),
        )
    } if group_names else {}

    targets = {}
    for item in items:
        item_target = frappe.utils.flt(item.get(PREPARATION_TIME_FIELD))
        group_target = group_targets.get(item.item_group, 0)
        if item_target > 0:
            targets[item.name] = {"minutes": item_target, "source": "Item"}
        elif group_target > 0:
            targets[item.name] = {"minutes": group_target, "source": "Item Group"}
        else:
            targets[item.name] = {"minutes": 0, "source": None}
    return targets


class OrderEntryItem(Document):
    pass
