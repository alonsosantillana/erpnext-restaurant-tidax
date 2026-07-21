# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
from datetime import date
import frappe
from frappe import _
from frappe.model.document import Document
import re


PRODUCTION_CENTER_ITEM_LIMIT = 500


def production_command_batch_key(item):
    ordered_time = frappe.utils.get_datetime(item.ordered_time) if item.ordered_time else None
    ordered_minute = ordered_time.strftime("%Y-%m-%d %H:%M") if ordered_time else "unknown"
    return f"{item.parent}:{frappe.utils.cint(item.ordered_nro) or 1}:{ordered_minute}"


class RestaurantObject(Document):
    @property
    def _room(self):
        return frappe.get_doc("Restaurant Object", self.room)

    def after_delete(self):
        frappe.publish_realtime(self.name, dict(
            action="Delete"
        ), after_commit=True)

    def on_update(self):
        self._on_update()

    def _on_update(self):
        frappe.publish_realtime(self.name, dict(
            action="Update",
            data=self.get_data() if self.type == "Room" else self.get_objects(self.name)[0]
        ))

        self.synchronize()

    def synchronize(self):
        if self.type == "Production Center":
            notification = dict(
                action="Notifications",
                orders_count=self.orders_count_in_production_center,
                current_user=self.current_user
            )
            frappe.publish_realtime(self.name, notification, after_commit=True)
            frappe.publish_realtime(
                "production_center_update",
                {
                    "center": self.name,
                    "orders_count": notification["orders_count"],
                },
                after_commit=True,
            )
        else:
            notification = dict(
                action="Notifications",
                orders_count=self.orders_count,
                current_user=self.current_user
            )
            if self.type == "Table":
                notification["ordered_items_qty"] = self.ordered_items_qty
                notification["guest_count"] = self.guest_count

            frappe.publish_realtime(self.name, notification, after_commit=True)

            if self.type != "Room":
                frappe.publish_realtime(self._room.name, dict(
                    action="Notifications",
                    orders_count=self._room.orders_count,
                    current_user=self.current_user
                ), after_commit=True)
                
    def validate_transaction(self, user=None):
        user = user or frappe.session.user
        if self.current_user is None or self.current_user == "Administrator" or self.orders_count == 0:
            frappe.db.set_value("Restaurant Object", self.name, "current_user", user)
            self.current_user = user
            return True

        if self.current_user != user and self.orders_count > 0:
            from restaurant_management.restaurant_management.restaurant_manage import check_exceptions
            if not check_exceptions(
                    dict(name="Restaurant Object", short_name="table", action="read", data=self),
                    _("The table {0} is Assigned to another User").format(self.description)
            ):
                frappe.throw(_("The table {0} is Assigned to another User").format(self.description))

    def validate_table(self):
        restaurant_settings = frappe.get_single("Restaurant Settings")
        if not restaurant_settings.multiple_pending_order and self.orders_count > 0:
            frappe.throw(_("Complete pending orders"))

    def add_order(self, client=None):
        # last_user = self.current_user
        self.validate_transaction()

        self.validate_table()

        from erpnext.stock.get_item_details import get_pos_profile
        # from erpnext.controllers.accounts_controller import get_default_taxes_and_charges

        company = frappe.defaults.get_user_default('company')
        pos_profile = get_pos_profile(company, user=frappe.session.user)

        order = frappe.new_doc("Table Order")
        if pos_profile:
            order.pos_profile = None if pos_profile is None else pos_profile.name
            order.customer = frappe.db.get_value('POS Profile', pos_profile.name, 'customer')
            taxes_and_charges = frappe.db.get_value('POS Profile', pos_profile.name, 'taxes_and_charges')
            # if taxes_and_charges is None:
            #    taxes = get_default_taxes_and_charges("Sales Taxes and Charges Template", company=company)
            #    taxes_and_charges = taxes.get("taxes_and_charges")

            order.taxes_and_charges = taxes_and_charges
        else:
            frappe.throw(_("POS Profile is required to use Point-of-Sale"))

        order.selling_price_list = pos_profile.selling_price_list
        order.table = self.name
        order.company = company

        order.save()
        response = dict(
            action="Add",
            data=order.data(),
            client=client,
            item_removed=None,
        )
        order.synchronize(dict(action="Add", client=client))
        return response

        # if last_user != frappe.session.user:
        #    self._on_update()

    @property
    def orders_count(self):
        if self.type == "Production Center":
            return self.orders_count_in_production_center

        return frappe.db.count("Table Order", {
            "room" if self.type == "Room" else "table": self.name,
            "status": "Attending"
        })

    @property
    def ordered_items_qty(self):
        if self.type != "Table":
            return 0

        active_orders = frappe.get_all("Table Order", filters={
            "table": self.name,
            "status": "Attending"
        }, pluck="name")
        if not active_orders:
            return 0

        quantities = frappe.get_all("Order Entry Item", filters={
            "parenttype": "Table Order",
            "parent": ("in", active_orders),
            "qty": (">", 0)
        }, pluck="qty")
        total = sum(frappe.utils.flt(qty) for qty in quantities)
        return int(total) if total.is_integer() else total

    @property
    def guest_count(self):
        if self.type != "Table":
            return 0

        guest_counts = frappe.get_all("Table Order", filters={
            "table": self.name,
            "status": "Attending"
        }, pluck="guest_count")
        return sum(frappe.utils.cint(value) for value in guest_counts)

    @property
    def orders_count_in_production_center(self):
        status_managed = self._status_managed
        items_group = self._items_group

        if len(status_managed) > 0 and len(items_group) > 0:
            return frappe.db.count("Order Entry Item", {
                "status": ("in", status_managed),
                "item_group": ("in", items_group),
                "parent": ("!=", ""),
                "qty": (">", "0")
            })

        return 0

    def _validate_production_center(self):
        if self.type != "Production Center":
            frappe.throw(_("This operation requires a Production Center"))
        if not self._status_managed or not self._items_group:
            frappe.throw(_("Configure statuses and item groups for Production Center {0}").format(self.description))

        permissions = frappe.permissions.get_doc_permissions(self)
        can_manage_all_rooms = (
            frappe.session.user == "Administrator"
            or permissions.get("write")
            or permissions.get("create")
        )
        if not can_manage_all_rooms:
            allowed_rooms = set(frappe.get_single("Restaurant Settings").rooms_access())
            if self.room not in allowed_rooms:
                frappe.throw(_("Not permitted to use Production Center {0}").format(self.description), frappe.PermissionError)

    @staticmethod
    def _production_company_and_profile():
        from erpnext.stock.get_item_details import get_pos_profile

        company = frappe.defaults.get_user_default("company")
        if not company:
            frappe.throw(_("Set a default Company before opening Production Center"))
        if not frappe.has_permission("Company", "read", company):
            frappe.throw(_("Not permitted to use Company {0}").format(company), frappe.PermissionError)

        pos_profile = get_pos_profile(company, user=frappe.session.user)
        if not pos_profile or pos_profile.get("disabled"):
            frappe.throw(_("No enabled POS Profile is available for {0}").format(company))
        return company, pos_profile.name

    def _production_status_map(self):
        return {
            row.status_managed: row.next_status
            for row in self.status_managed
            if row.status_managed and row.next_status
        }

    @staticmethod
    def _production_order_data(company, pos_profile):
        fields = [
            "name",
            "owner",
            "cambio_mozo",
            "cambio_mozo_nombre",
            "comentario",
            "room_description",
            "table_description",
        ]
        today = frappe.utils.nowdate()
        tomorrow = frappe.utils.add_days(today, 1)
        active_orders = frappe.get_all(
            "Table Order",
            filters={
                "company": company,
                "pos_profile": pos_profile,
                "status": ("!=", "Invoiced"),
            },
            fields=fields,
            order_by="modified desc",
            limit_page_length=PRODUCTION_CENTER_ITEM_LIMIT,
        )
        recent_orders = frappe.get_all(
            "Table Order",
            filters=[
                ["company", "=", company],
                ["pos_profile", "=", pos_profile],
                ["modified", ">=", today],
                ["modified", "<", tomorrow],
            ],
            fields=fields,
            order_by="modified desc",
            limit_page_length=0,
        )
        return {row.name: row for row in [*active_orders, *recent_orders]}

    @staticmethod
    def _waiter_names(orders):
        users = {
            (order.cambio_mozo or order.owner)
            for order in orders.values()
            if order.cambio_mozo or order.owner
        }
        if not users:
            return {}
        return {
            row.name: row.full_name
            for row in frappe.get_all(
                "User",
                filters={"name": ("in", list(users))},
                fields=["name", "full_name"],
                limit_page_length=len(users),
            )
        }

    def _group_production_commands(self, items, orders, status_map):
        waiter_names = self._waiter_names(orders)
        commands = {}
        for item in items:
            order = orders.get(item.parent, frappe._dict())
            batch_key = production_command_batch_key(item)
            key = batch_key
            waiter = order.cambio_mozo or order.owner
            command = commands.setdefault(
                key,
                {
                    "key": key,
                    "order_name": item.parent,
                    "short_name": self.order_short_name(item.parent),
                    "table_description": order.table_description or item.table_description,
                    "room_description": order.room_description,
                    "waiter": order.cambio_mozo_nombre or waiter_names.get(waiter) or waiter,
                    "comment": order.comentario,
                    "ordered_time": item.ordered_time,
                    "identifiers": [],
                    "items": [],
                    "qty": 0,
                },
            )
            command["identifiers"].append(item.identifier)
            command["items"].append({
                "identifier": item.identifier,
                "item_code": item.item_code,
                "item_name": item.item_name,
                "qty": frappe.utils.flt(item.qty),
                "notes": item.notes,
                "status": item.status,
                "next_status": status_map.get(item.status),
            })
            command["qty"] += frappe.utils.flt(item.qty)

        for command in commands.values():
            statuses = list(dict.fromkeys(item["status"] for item in command["items"]))
            command["statuses"] = statuses
            command["status"] = statuses[0] if len(statuses) == 1 else "Mixed"
            command["next_status"] = status_map.get(command["status"])

        return sorted(
            commands.values(),
            key=lambda command: frappe.utils.get_datetime(command["ordered_time"]),
        )

    @staticmethod
    def _production_consolidation(items, active_statuses):
        consolidation = {}
        active_status_list = list(active_statuses)
        active_statuses = set(active_status_list)
        pending_status = active_status_list[0] if active_status_list else None
        for item in items:
            row = consolidation.setdefault(
                item.item_code,
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "pending_qty": 0,
                    "processing_qty": 0,
                    "completed_qty": 0,
                    "total_qty": 0,
                },
            )
            quantity = frappe.utils.flt(item.qty)
            if item.status == pending_status:
                row["pending_qty"] += quantity
            elif item.status in active_statuses:
                row["processing_qty"] += quantity
            else:
                row["completed_qty"] += quantity
            row["total_qty"] += quantity
        return consolidation

    def production_center_dashboard(self):
        self._validate_production_center()
        company, pos_profile = self._production_company_and_profile()

        status_map = self._production_status_map()
        active_statuses = list(status_map)
        attended_statuses = list(dict.fromkeys(
            next_status
            for next_status in status_map.values()
            if next_status not in active_statuses
        ))
        daily_statuses = list(dict.fromkeys([*active_statuses, *attended_statuses]))
        item_groups = list(dict.fromkeys(self._items_group))
        orders = self._production_order_data(company, pos_profile)
        order_names = list(orders)
        today = frappe.utils.nowdate()
        tomorrow = frappe.utils.add_days(today, 1)

        item_fields = [
            "name",
            "identifier",
            "parent",
            "item_code",
            "item_name",
            "item_group",
            "qty",
            "notes",
            "status",
            "ordered_time",
            "ordered_nro",
            "ordered_finish",
            "table_description",
            "modified",
        ]
        active_items = []
        daily_items = []
        if order_names:
            active_items = frappe.get_all(
                "Order Entry Item",
                filters={
                    "parent": ("in", order_names),
                    "status": ("in", active_statuses),
                    "item_group": ("in", item_groups),
                    "qty": (">", 0),
                },
                fields=item_fields,
                order_by="ordered_time asc",
                limit_page_length=PRODUCTION_CENTER_ITEM_LIMIT + 1,
            )
            if daily_statuses:
                daily_items = frappe.get_all(
                    "Order Entry Item",
                    filters=[
                        ["parent", "in", order_names],
                        ["status", "in", daily_statuses],
                        ["item_group", "in", item_groups],
                        ["qty", ">", 0],
                        ["ordered_time", ">=", today],
                        ["ordered_time", "<", tomorrow],
                    ],
                    fields=item_fields,
                    order_by="ordered_time asc",
                    limit_page_length=0,
                )

        active_truncated = len(active_items) > PRODUCTION_CENTER_ITEM_LIMIT
        active_items = active_items[:PRODUCTION_CENTER_ITEM_LIMIT]
        active_status_set = set(active_statuses)
        attended_status_set = set(attended_statuses)
        active_batch_keys = {
            production_command_batch_key(item)
            for item in active_items
        }
        active_batch_keys.update(
            production_command_batch_key(item)
            for item in daily_items
            if item.status in active_status_set
        )
        command_items_by_identifier = {
            item.identifier: item
            for item in active_items
        }
        for item in daily_items:
            if production_command_batch_key(item) in active_batch_keys:
                command_items_by_identifier.setdefault(item.identifier, item)
        command_items = sorted(
            command_items_by_identifier.values(),
            key=lambda item: frappe.utils.get_datetime(item.ordered_time),
        )
        attended_items = [
            item
            for item in daily_items
            if item.status in attended_status_set
            and production_command_batch_key(item) not in active_batch_keys
        ]
        consolidation = self._production_consolidation(daily_items, active_statuses)

        commands = self._group_production_commands(command_items, orders, status_map)
        attended = self._group_production_commands(attended_items, orders, {})
        active_qty = sum(frappe.utils.flt(item.qty) for item in active_items)
        daily_qty = sum(frappe.utils.flt(item.qty) for item in daily_items)
        completed_qty = sum(
            frappe.utils.flt(item.qty)
            for item in daily_items
            if item.status in attended_status_set
        )
        attended_qty = sum(frappe.utils.flt(item.qty) for item in attended_items)

        return {
            "center": {
                "name": self.name,
                "description": self.description,
                "statuses": active_statuses,
                "item_groups": item_groups,
            },
            "period": {
                "date": today,
                "start": today,
                "end_exclusive": tomorrow,
            },
            "counts": {
                "active_items": len(active_items),
                "active_qty": active_qty,
                "daily_items": len(daily_items),
                "daily_qty": daily_qty,
                "completed_qty": completed_qty,
                "commands": len(commands),
                "consolidated_items": len(consolidation),
                "attended_commands": len(attended),
                "attended_qty": attended_qty,
            },
            "commands": commands,
            "consolidation": sorted(
                consolidation.values(),
                key=lambda row: (row["item_name"] or row["item_code"]),
            ),
            "attended": attended,
            "can_transition": frappe.has_permission("Restaurant Object", "write", doc=self),
            "truncated": {
                "active": active_truncated,
                "attended": False,
            },
        }

    def orders_list(self, name=None):
        orders = frappe.get_all("Table Order", fields="name", filters={
            "table" if name is None else "name": name if name is not None else self.name,
            "status": "Attending"
        })
        for order in orders:
            data = frappe.get_doc("Table Order", order.name).short_data()
            for field in data:
                order[field] = data[field]

        return orders

    def get_objects(self, name=None):
        tables = frappe.get_all("Restaurant Object", "name", filters={
            "room" if name is None else "name": self.name if name is None else name,
            "type": ("!=", "Room")
        })

        for table in tables:
            data = frappe.get_doc("Restaurant Object", table.name).get_data()
            for prop in data:
                table[prop] = data[prop]

        return tables

    def get_data(self):
        fields = ["name", "description", "orders_count"] if self.type == "Room" \
            else ["name", "type", "description", "no_of_seats", "identifier", "orders_count",
                  "data_style", "min_size", "current_user", "color", 'shape']
        data = {}

        for field in fields:
            data[field] = getattr(self, field)

        if self.type == "Table":
            data["ordered_items_qty"] = self.ordered_items_qty
            data["guest_count"] = self.guest_count

        if self.type == "Production Center":
            data["status_managed"] = self._status_managed
            data["items_group"] = self._items_group
        return data

    @property
    def min_size(self):
        return 80

    @property
    def css_style(self):
        return f'{self.style}; background-color:{self.color};'

    @property
    def identifier(self):
        return self.name  # f"{'room' if self.type == 'Room' else 'table'}_{self.name}"

    def add_object(self, t="Table"):
        import random

        objects_count = frappe.db.count("Restaurant Object", filters={"room": self.name})
        table = frappe.new_doc("Restaurant Object")

        zIndex = objects_count + 60
        left = objects_count * 25 + (0 if t == 'Table' else 200)
        top = objects_count * 25
        colors = ["#5b1e34", "#97264f", "#1a4469", "#1579d0", "#2d401d", "#2e844e", "#505a62"]
        color = colors[random.randint(0, 6)]

        data_style = f'"x":"{left}","y":"{top}","z-index":"{zIndex}","width":"100px","height":"100px"'
        table.type = t
        table.room = self.name
        table.data_style = "{" + data_style + "}"
        table.color = color
        table.description = f"{t[:1]}{(objects_count + 1)}"
        table.no_of_seats = 4
        table.shape = 'Square'
        table.save()

        frappe.publish_realtime(
            "order_entry_update", self, after_commit=True
        )
        data = self.get_objects(table.name)

        if len(data) > 0:
            frappe.publish_realtime(self.name, dict(
                action="Add",
                table=data[0]
            ), after_commit=True)
            return data[0]

    def count_objects(self, t):
        return frappe.db.count("Restaurant Object", filters={
            "room": self.name, "type": t
        })

    def set_status_command(self, identifier, tiempo=None, expected_status=None):
        current_status = frappe.db.get_value(
            "Order Entry Item", {"identifier": identifier}, "status"
        )
        return self.set_commands_status(
            identifiers=[identifier],
            expected_status=expected_status or current_status,
        )

    def set_commands_status(self, identifiers, expected_status):
        self._validate_production_center()
        company, pos_profile = self._production_company_and_profile()
        identifiers = frappe.parse_json(identifiers) if isinstance(identifiers, str) else identifiers
        if not isinstance(identifiers, list) or not identifiers:
            frappe.throw(_("Select at least one kitchen item"))

        identifiers = list(dict.fromkeys(identifiers))
        if len(identifiers) > 100:
            frappe.throw(_("A maximum of 100 kitchen items can be changed at once"))

        status_map = self._production_status_map()
        if expected_status not in status_map:
            frappe.throw(_("Status {0} is not managed by this Production Center").format(expected_status))
        next_status = status_map[expected_status]

        entries = frappe.get_all(
            "Order Entry Item",
            filters={"identifier": ("in", identifiers)},
            fields=[
                "name",
                "identifier",
                "parent",
                "item_group",
                "status",
                "ordered_time",
                "ordered_finish",
            ],
            limit_page_length=len(identifiers),
        )
        if len(entries) != len(identifiers):
            frappe.throw(_("One or more kitchen items no longer exist"))

        allowed_groups = set(self._items_group)
        for entry in entries:
            if entry.item_group not in allowed_groups:
                frappe.throw(_("A kitchen item is outside this Production Center"), frappe.PermissionError)
            if entry.status != expected_status:
                frappe.throw(
                    _("The command changed in another screen. Reloading current data."),
                    frappe.ValidationError,
                )

        order_names = {entry.parent for entry in entries}
        permitted_orders = set(frappe.get_all(
            "Table Order",
            filters={
                "name": ("in", list(order_names)),
                "company": company,
                "pos_profile": pos_profile,
            },
            pluck="name",
            limit_page_length=len(order_names),
        ))
        if permitted_orders != order_names:
            frappe.throw(_("A kitchen item is outside the active company or POS Profile"), frappe.PermissionError)

        now = frappe.utils.now_datetime()
        for entry in entries:
            values = {"status": next_status}
            if next_status == "Completed" and not frappe.utils.cint(entry.ordered_finish):
                elapsed_seconds = max(
                    0,
                    frappe.utils.time_diff_in_seconds(now, entry.ordered_time or now),
                )
                values["ordered_finish"] = max(1, int(elapsed_seconds / 60))
            frappe.db.set_value("Order Entry Item", entry.name, values)

        for order_name in order_names:
            order = frappe.get_doc("Table Order", order_name)
            order.synchronize(dict(status=[expected_status, next_status]))

        return {
            "updated": identifiers,
            "previous_status": expected_status,
            "status": next_status,
        }
    
    # TIDAX: GUARDA TIEMPO DE DEMORA DEL PLATO
    def tiempo_demora(self, tiempo):
        if(tiempo):
            # Usamos una expresión regular para dividir la cadena
            resultado = re.match(r'(\d+) ([a-zA-Z]+)', tiempo)
            if resultado:
                if(resultado.group(1)):
                    numero = int(resultado.group(1))  # Obtenemos la parte numérica
                if(resultado.group(2)):
                    letra = resultado.group(2)  # Obtenemos la parte de letras
            else:
                print("No se encontró una coincidencia válida en la cadena.")
                letra = "Now"
            
            if(letra == "m"):
                numero = numero
            elif(letra == "h"):
                numero = numero * 60
            else:
                numero = 1
        return numero

    def command_data(self, command):
        item = self.commands_food(command)
        return {"data": item[0]} if len(item) > 0 else None

    def commands_food(self, identifier=None, last_status=None):
        status_managed = self.status_managed

        filters = {
            "status": ("in", [item.status_managed for item in status_managed]),
            "item_group": ("in", self._items_group),
            "parent": ("!=", ""),
            "qty": (">", "0")
        } if identifier is None else {
            "identifier": identifier
        }

        items = []
        for entry in frappe.get_all("Order Entry Item", "*", filters=filters, order_by="ordered_time"):
            items.append(self.get_command_data(entry, last_status))

        return items

    def get_command_data(self, entry, las_status=None):
        return dict(
            identifier=entry.identifier,
            item_group=entry.item_group,
            item_code=entry.item_code,
            item_name=entry.item_name,
            order_name=entry.parent,
            table_description=entry.table_description,
            short_name=self.order_short_name(entry.parent),
            qty=entry.qty,
            rate=entry.rate,
            amount=(entry.qty * entry.rate),
            entry_name=entry.name,
            status=entry.status,
            last_status=las_status,
            notes=entry.notes,
            ordered_time=entry.ordered_time or frappe.utils.now_datetime(),#frappe.format_value(entry.creation, {"fieldtype": "Datetime"}),
            ordered_nro=entry.ordered_nro or 1,
            process_status_data=self.process_status_data(entry)
        )

    def process_status_data(self, item):
        return dict(
            next_action_message=self._status(item.status)["action_message"],
            color=self._status(item.status)["color"],
            icon=self._status(item.status)["icon"],
            status_message=self._status(item.status)["message"]
        )

    @staticmethod
    def order_short_name(order_name):
        return order_name[8:]

    def next_status(self, last_status):
        status_managed = self.status_managed
        for status in status_managed:
            if last_status == status.status_managed:
                return status.next_status

        return "Processing"

    @staticmethod
    def _status(status="Pending"):
        _status = dict(
            Pending=dict(icon="fa fa-cart-arrow-down", color="#D49B00", message=_("Pending to send"), action_message="Add"),
            Attending=dict(icon="fa fa-cart-arrow-down", color="#D49B00", message=_("Pending to send"), action_message="Sent"),
            Sent=dict(icon="fa fa-paper-plane-o", color="steelblue", message="Waiting", action_message="Confirm"),
            Processing=dict(icon="fa fa-gear", color="#618685", message="Processing", action_message="Complete"),
            Completed=dict(icon="fa fa-check", color="green", message="Completed", action_message="Deliver"),
            Delivering=dict(icon="fa fa-reply", color="#ff7b25", message="Delivering", action_message="Deliver"),
            Delivered=dict(icon="fa fa-cutlery", color="green", message='Delivered', action_message="Invoice"),
            Invoiced=dict(icon="fa fa-money", color="green", message="Invoiced", action_message="Invoiced"),
        )
        return _status[status] if status in _status else _status["Pending"]

    @staticmethod
    def status_list():
        return ["Pending"]

    @property
    def _status_managed(self):
        return [item.status_managed for item in self.status_managed]

    @property
    def _items_group(self):
        items_groups = []
        for group in self.production_center_group:
            lft, rgt = frappe.db.get_value('Item Group', group.item_group, ['lft', 'rgt'])

            for item in frappe.get_all("Item Group", "name", filters={
                "lft": (">=", lft),
                "rgt": ("<=", rgt)
            }):
                items_groups.append(item.name)

        return items_groups
    
    # TIDAX
    @property
    def _production_center(self):
        productions_centers = []
        for group in self.production_center_group:
            lft, rgt = frappe.db.get_value('Item Group', group.item_group, ['lft', 'rgt'])

            for item in frappe.get_list("Item Group", "name", filters={
                "lft": (">=", lft),
                "rgt": ("<=", rgt)
            }):
                productions_centers.append(group.description)

        return productions_centers

    def set_style(self, data, shape=None):
        _data = data
        if shape and self.type == "Production Center":
            _data = "Square"

        frappe.db.set_value("Restaurant Object", self.name, "shape" if shape else 'data_style', _data)
        self._on_update()

    def _delete(self):
        deleted = {
            "name": self.name,
            "type": self.type,
            "room": self.room,
        }
        self.delete()
        return deleted


def load_json(data):
    import json
    try:
        _data = json.loads("{}" if data is None else data)
    except ValueError as e:
        _data = []

    return _data
