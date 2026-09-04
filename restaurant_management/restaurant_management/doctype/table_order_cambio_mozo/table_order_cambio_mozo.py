# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, get_datetime, getdate

from restaurant_management.restaurant_management.company_settings import (
    get_restaurant_settings,
    get_user_restaurant_company,
)


DOCTYPE = "Table Order Cambio Mozo"
WAITER_ROLES = {"Mozo", "resto_mozo"}
MAX_ORDERS = 500


def _require_authenticated_user():
    if frappe.session.user == "Guest":
        frappe.throw(_("Authentication required"), frappe.AuthenticationError)


def _validate_company(company):
    _require_authenticated_user()
    if not company:
        frappe.throw(_("Seleccione una compañía"))
    active_company = get_user_restaurant_company()
    if active_company and company != active_company:
        frappe.throw(
            _("No tiene permiso para operar con la compañía {0}").format(company),
            frappe.PermissionError,
        )
    if not frappe.has_permission("Company", "read", company):
        frappe.throw(
            _("No tiene permiso para operar con la compañía {0}").format(company),
            frappe.PermissionError,
        )
    get_restaurant_settings(company=company)
    return company


def _require_form_permission(permission_type="create"):
    _require_authenticated_user()
    if not frappe.has_permission(DOCTYPE, permission_type):
        frappe.throw(_("No tiene permiso para reasignar mozos"), frappe.PermissionError)


def _allowed_rooms(company):
    object_permissions = frappe.permissions.get_doc_permissions(
        frappe.new_doc("Restaurant Object")
    )
    if (
        frappe.session.user == "Administrator"
        or object_permissions.get("create")
        or object_permissions.get("write")
    ):
        return set(
            frappe.get_all(
                "Restaurant Object",
                filters={"type": "Room", "company": company},
                pluck="name",
            )
        )
    return set(get_restaurant_settings(company=company).rooms_access())


def _effective_waiter(order):
    return order.get("cambio_mozo") or order.get("owner")


def _user_names(users):
    users = {user for user in users if user}
    if not users:
        return {}
    return {
        row.name: row.full_name or row.name
        for row in frappe.get_all(
            "User",
            filters={"name": ("in", list(users))},
            fields=["name", "full_name"],
            limit_page_length=len(users),
        )
    }


def _parse_filters(filters):
    parsed = frappe.parse_json(filters) if isinstance(filters, str) else filters
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        frappe.throw(_("Los filtros deben ser un objeto"))
    return parsed


@frappe.whitelist()
def get_available_orders(fecha, company, room=None, mozo_origen=None):
    _require_form_permission("create")
    company = _validate_company(company)
    if not fecha:
        frappe.throw(_("Seleccione una fecha"))

    allowed_rooms = _allowed_rooms(company)
    if room and room not in allowed_rooms:
        frappe.throw(
            _("No tiene permiso para el ambiente seleccionado"),
            frappe.PermissionError,
        )
    if not allowed_rooms:
        return []

    start = get_datetime(f"{getdate(fecha)} 00:00:00")
    end = get_datetime(f"{getdate(fecha)} 23:59:59.999999")
    filters = {
        "company": company,
        "status": "Attending",
        "docstatus": ("<", 2),
        "service_type": "Dine In",
        "table": ("is", "set"),
        "room": ("in", list(allowed_rooms)),
        "creation": ("between", [start, end]),
    }
    if room:
        filters["room"] = room

    orders = frappe.get_all(
        "Table Order",
        filters=filters,
        fields=[
            "name", "owner", "cambio_mozo", "table", "table_description",
            "room", "room_description", "customer", "customer_name",
            "guest_count", "amount", "status", "pos_profile",
        ],
        order_by="room_description asc, table_description asc, creation asc",
        limit_page_length=MAX_ORDERS + 1,
    )
    if len(orders) > MAX_ORDERS:
        frappe.throw(
            _("Hay más de {0} órdenes. Use los filtros de ambiente o mozo.").format(
                MAX_ORDERS
            )
        )

    names = _user_names({_effective_waiter(order) for order in orders})
    result = []
    for order in orders:
        waiter = _effective_waiter(order)
        if mozo_origen and waiter != mozo_origen:
            continue
        result.append({
            "seleccionar": 1,
            "orden": order.name,
            "table": order.table,
            "table_description": order.table_description or order.table,
            "room": order.room,
            "room_description": order.room_description or order.room,
            "mozo": waiter,
            "mozo_nombre": names.get(waiter, waiter),
            "customer": order.customer,
            "customer_name": order.customer_name,
            "guest_count": order.guest_count,
            "amount": order.amount,
            "status": order.status,
            "pos_profile": order.pos_profile,
        })
    return result


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_current_waiters(doctype, txt, searchfield, start, page_len, filters):
    _require_form_permission("create")
    if doctype != "User":
        frappe.throw(_("Tipo de enlace no permitido"), frappe.PermissionError)

    parsed_filters = _parse_filters(filters)
    orders = get_available_orders(
        fecha=parsed_filters.get("fecha"),
        company=parsed_filters.get("company"),
        room=parsed_filters.get("room"),
    )
    search_text = (txt or "").casefold()
    waiters = {}
    for order in orders:
        user = order.get("mozo")
        full_name = order.get("mozo_nombre") or user
        if not user:
            continue
        if (
            search_text
            and search_text not in user.casefold()
            and search_text not in full_name.casefold()
        ):
            continue
        waiters[user] = full_name

    rows = sorted(waiters.items(), key=lambda row: (row[1].casefold(), row[0]))
    start = max(0, cint(start))
    page_len = min(max(1, cint(page_len)), 100)
    return rows[start:start + page_len]


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def search_waiters(doctype, txt, searchfield, start, page_len, filters):
    _require_form_permission("create")
    if doctype != "User":
        frappe.throw(_("Tipo de enlace no permitido"), frappe.PermissionError)

    parsed_filters = _parse_filters(filters)
    company = _validate_company(parsed_filters.get("company"))
    room = parsed_filters.get("room")
    if room and room not in _allowed_rooms(company):
        frappe.throw(
            _("No tiene permiso para el ambiente seleccionado"),
            frappe.PermissionError,
        )

    profiles = frappe.get_all(
        "POS Profile",
        filters={"company": company, "disabled": 0},
        pluck="name",
    )
    if not profiles:
        return []

    room_condition = ""
    values = {
        "profiles": tuple(profiles),
        "roles": tuple(WAITER_ROLES),
        "text": f"%{txt or ''}%",
        "start": max(0, cint(start)),
        "page_len": min(max(1, cint(page_len)), 100),
    }
    if room:
        room_condition = """
            and exists (
                select 1
                from `tabRestaurant Permission` permission
                where permission.parent = profile_user.name
                    and permission.parenttype = 'Restaurant Permission Manage'
                    and permission.room = %(room)s
            )
        """
        values["room"] = room

    return frappe.db.sql(
        f"""
        select distinct user.name, coalesce(nullif(user.full_name, ''), user.name)
        from `tabUser` user
        inner join `tabPOS Profile User` profile_user
            on profile_user.user = user.name
            and profile_user.parenttype = 'POS Profile'
            and profile_user.parent in %(profiles)s
        inner join `tabHas Role` user_role
            on user_role.parent = user.name
            and user_role.parenttype = 'User'
            and user_role.role in %(roles)s
        where user.enabled = 1
            and user.user_type = 'System User'
            and (user.name like %(text)s or user.full_name like %(text)s)
            {room_condition}
        order by user.full_name asc, user.name asc
        limit %(start)s, %(page_len)s
        """,
        values,
        as_list=True,
    )


class TableOrderCambioMozo(Document):
    def before_insert(self):
        self.company = self.company or get_user_restaurant_company()

    def validate(self):
        _validate_company(self.company)
        if not self.orden_fecha:
            frappe.throw(_("Seleccione una fecha"))
        if not self.nuevo_mozo:
            frappe.throw(_("Seleccione el nuevo mozo"))
        self._validate_target_user()

        selected = self._selected_rows()
        if not selected:
            frappe.throw(_("Seleccione por lo menos una orden"))
        order_names = [row.orden for row in selected if row.orden]
        duplicates = sorted(
            {name for name in order_names if order_names.count(name) > 1}
        )
        if duplicates:
            frappe.throw(
                _("Hay órdenes duplicadas: {0}").format(", ".join(duplicates))
            )
        if any(not row.orden for row in selected):
            frappe.throw(_("Todas las filas seleccionadas deben tener una orden"))

    def before_submit(self):
        selected = self._selected_rows()
        self.set("orden_item", selected)
        orders = self._validated_orders(selected, lock=True)
        target_name = (
            frappe.db.get_value("User", self.nuevo_mozo, "full_name")
            or self.nuevo_mozo
        )

        affected_tables = set()
        for row in selected:
            order = orders[row.orden]
            frappe.db.set_value(
                "Table Order",
                order.name,
                {
                    "cambio_mozo": self.nuevo_mozo,
                    "cambio_mozo_nombre": target_name,
                },
            )
            row.mozo_cambio = self.nuevo_mozo
            row.mozo_cambio_nombre = target_name
            if order.table:
                affected_tables.add(order.table)

        self._refresh_table_owners(affected_tables)
        self.transferred_count = len(selected)
        self.resultado = _("{0} orden(es) reasignadas a {1} ({2})").format(
            len(selected), target_name, self.nuevo_mozo
        )

        for row in selected:
            order_doc = frappe.get_doc("Table Order", row.orden)
            order_doc.add_comment(
                "Info",
                _("Mozo reasignado de {0} a {1} mediante {2}").format(
                    row.mozo_nombre or row.mozo,
                    target_name,
                    self.name,
                ),
            )
            order_doc.synchronize({"action": "Update"})

    def before_cancel(self):
        frappe.throw(
            _(
                "Una reasignación ejecutada no puede cancelarse. "
                "Cree una nueva reasignación para devolver las órdenes."
            )
        )

    def _selected_rows(self):
        return [
            row for row in self.get("orden_item") or [] if cint(row.seleccionar)
        ]

    def _validate_target_user(self):
        user = frappe.db.get_value(
            "User",
            self.nuevo_mozo,
            ["name", "enabled", "user_type"],
            as_dict=True,
        )
        if not user or not user.enabled or user.user_type != "System User":
            frappe.throw(_("El nuevo mozo debe ser un usuario activo del sistema"))
        if not WAITER_ROLES.intersection(frappe.get_roles(self.nuevo_mozo)):
            frappe.throw(_("El usuario seleccionado no tiene rol de mozo"))

    def _validated_orders(self, selected, lock=False):
        order_names = sorted({row.orden for row in selected})
        lock_clause = " for update" if lock else ""
        rows = frappe.db.sql(
            f"""
            select
                name, owner, cambio_mozo, company, creation, docstatus, status,
                service_type, `table`, table_description, room, room_description,
                customer, customer_name, guest_count, amount, pos_profile
            from `tabTable Order`
            where name in %(names)s
            order by name
            {lock_clause}
            """,
            {"names": tuple(order_names)},
            as_dict=True,
        )
        orders = {row.name: row for row in rows}
        missing = [name for name in order_names if name not in orders]
        if missing:
            frappe.throw(
                _("No se encontraron las órdenes: {0}").format(", ".join(missing))
            )

        allowed_rooms = _allowed_rooms(self.company)
        current_names = _user_names(
            {_effective_waiter(order) for order in rows}
        )
        target_name = (
            frappe.db.get_value("User", self.nuevo_mozo, "full_name")
            or self.nuevo_mozo
        )

        for detail in selected:
            order = orders[detail.orden]
            current_waiter = _effective_waiter(order)
            if order.company != self.company:
                frappe.throw(
                    _("La orden {0} pertenece a otra compañía").format(order.name)
                )
            if getdate(order.creation) != getdate(self.orden_fecha):
                frappe.throw(
                    _("La orden {0} no pertenece a la fecha seleccionada").format(
                        order.name
                    )
                )
            if order.docstatus == 2 or order.status != "Attending":
                frappe.throw(_("La orden {0} ya no está activa").format(order.name))
            if (
                order.service_type != "Dine In"
                or not order.table
                or not order.room
            ):
                frappe.throw(
                    _("La orden {0} no corresponde a una mesa").format(order.name)
                )
            if order.room not in allowed_rooms:
                frappe.throw(
                    _("No tiene permiso para el ambiente de la orden {0}").format(
                        order.name
                    ),
                    frappe.PermissionError,
                )
            if self.mozo_origen and current_waiter != self.mozo_origen:
                frappe.throw(
                    _("La orden {0} ya no pertenece al mozo de origen").format(
                        order.name
                    )
                )
            if detail.mozo and detail.mozo != current_waiter:
                frappe.throw(
                    _(
                        "La orden {0} fue reasignada por otro usuario. "
                        "Recargue las órdenes."
                    ).format(order.name)
                )
            if current_waiter == self.nuevo_mozo:
                frappe.throw(
                    _("La orden {0} ya pertenece al nuevo mozo").format(order.name)
                )

            self._validate_waiter_access(order)
            detail.mozo = current_waiter
            detail.mozo_nombre = current_names.get(current_waiter, current_waiter)
            detail.mozo_cambio = self.nuevo_mozo
            detail.mozo_cambio_nombre = target_name
            detail.table = order.table
            detail.table_description = order.table_description or order.table
            detail.room = order.room
            detail.room_description = order.room_description or order.room
            detail.customer = order.customer
            detail.customer_name = order.customer_name
            detail.guest_count = order.guest_count
            detail.amount = order.amount
            detail.status = order.status
            detail.pos_profile = order.pos_profile

        return orders

    def _validate_waiter_access(self, order):
        profile_user = frappe.db.get_value(
            "POS Profile User",
            {
                "parent": order.pos_profile,
                "parenttype": "POS Profile",
                "user": self.nuevo_mozo,
            },
            "name",
        )
        if not profile_user:
            frappe.throw(
                _("El nuevo mozo no está asignado al Perfil POS {0}").format(
                    order.pos_profile
                )
            )
        if not frappe.db.exists(
            "Restaurant Permission",
            {
                "parent": profile_user,
                "parenttype": "Restaurant Permission Manage",
                "room": order.room,
            },
        ):
            frappe.throw(
                _("El nuevo mozo no tiene acceso al ambiente {0}").format(
                    order.room_description or order.room
                )
            )

    def _refresh_table_owners(self, tables):
        for table in tables:
            active_orders = frappe.get_all(
                "Table Order",
                filters={
                    "table": table,
                    "company": self.company,
                    "status": "Attending",
                    "docstatus": ("<", 2),
                },
                fields=["owner", "cambio_mozo"],
            )
            waiters = {_effective_waiter(order) for order in active_orders}
            waiters.discard(None)
            if len(waiters) == 1:
                frappe.db.set_value(
                    "Restaurant Object",
                    table,
                    "current_user",
                    next(iter(waiters)),
                    update_modified=False,
                )
