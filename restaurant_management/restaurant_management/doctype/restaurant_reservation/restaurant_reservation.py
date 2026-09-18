from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import add_days, add_to_date, cint, get_datetime, now_datetime

from restaurant_management.restaurant_management.company_settings import (
    get_restaurant_settings,
    get_user_restaurant_company,
)
from restaurant_management.restaurant_management.pos_series import (
    get_company_reservation_series,
)


BLOCKING_STATUSES = ("Pending", "Confirmed", "Arrived", "Seated")
TERMINAL_STATUSES = ("Completed", "No Show", "Cancelled")
ACTION_ROLES = {
    "System Manager",
    "resto_admin",
    "resto_reservas",
    "resto_cajero",
    "resto_mozo",
}
ALLOWED_TRANSITIONS = {
    "Pending": {"Confirmed", "Cancelled", "No Show"},
    "Confirmed": {"Arrived", "Seated", "Cancelled", "No Show"},
    "Arrived": {"Seated", "Cancelled", "No Show"},
    "Seated": {"Completed"},
}


class RestaurantReservation(Document):
    def autoname(self):
        self.company = self.company or get_user_restaurant_company()
        if not self.company:
            frappe.throw(_("Seleccione la compañía de la reserva"))
        self.naming_series = get_company_reservation_series(self.company)
        self.name = make_autoname(self.naming_series, doc=self)

    def validate(self):
        self._validate_status_change()
        settings = self._get_settings()
        self._validate_company_context(settings)
        self._validate_schedule(settings)
        self._validate_guest()
        self._validate_tables(settings)

    def on_update(self):
        self.publish_update()

    def on_trash(self):
        if self.table_order:
            frappe.throw(_("No puede eliminar una reserva que ya tiene una orden"))

    def after_delete(self):
        self.publish_update()

    def _get_settings(self):
        settings = get_restaurant_settings(company=self.company)
        if not cint(settings.get("enable_reservations")):
            frappe.throw(
                _("Active Reservas de mesas en la configuración de {0}").format(
                    self.company
                )
            )
        return settings

    def _validate_status_change(self):
        if self.is_new():
            if not self.status:
                self.status = "Pending"
            if self.status != "Pending":
                frappe.throw(_("Una reserva nueva debe iniciar como Pendiente"))
            return

        previous = self.get_doc_before_save()
        if (
            previous
            and previous.status != self.status
            and not self.flags.get("reservation_status_action")
        ):
            frappe.throw(_("Use las acciones de la reserva para cambiar su estado"))

    def _validate_company_context(self, settings):
        if not frappe.has_permission("Company", "read", self.company):
            frappe.throw(
                _("No tiene permiso para usar la compañía {0}").format(self.company),
                frappe.PermissionError,
            )

        if not self.pos_profile:
            self.pos_profile = settings.get("pos_profile")
        profile_company = (
            frappe.db.get_value("POS Profile", self.pos_profile, "company")
            if self.pos_profile
            else None
        )
        if not profile_company or profile_company != self.company:
            frappe.throw(_("El perfil POS debe pertenecer a la compañía de la reserva"))

        if self.customer and frappe.db.get_value("Customer", self.customer, "disabled"):
            frappe.throw(_("El cliente seleccionado está deshabilitado"))

    def _validate_schedule(self, settings):
        if not self.reservation_from or not self.reservation_to:
            frappe.throw(_("Ingrese el inicio y fin de la reserva"))
        start = get_datetime(self.reservation_from)
        end = get_datetime(self.reservation_to)
        if not start or not end or end <= start:
            frappe.throw(_("La hora final debe ser posterior a la hora inicial"))

        max_advance_days = cint(settings.get("reservation_max_advance_days") or 0)
        if max_advance_days and start.date() > add_days(now_datetime(), max_advance_days).date():
            frappe.throw(
                _("La reserva supera el máximo de {0} días de anticipación").format(
                    max_advance_days
                )
            )

    def _validate_guest(self):
        if cint(self.guest_count) < 1:
            frappe.throw(_("La reserva debe tener al menos un comensal"))
        if not (self.guest_name or "").strip():
            frappe.throw(_("Ingrese el nombre de la reserva"))
        if not (self.phone or "").strip():
            frappe.throw(_("Ingrese el teléfono de contacto"))

    def _validate_tables(self, settings):
        rows = list(self.get("reservation_tables") or [])
        tables_required = self.status != "Pending" or not cint(
            settings.get("allow_unassigned_reservations")
        )
        if not rows:
            if tables_required:
                frappe.throw(_("Asigne al menos una mesa a la reserva"))
            return

        table_names = [row.restaurant_table for row in rows]
        if len(table_names) != len(set(table_names)):
            frappe.throw(_("Una mesa no puede repetirse en la misma reserva"))

        contexts = {
            row.name: row
            for row in frappe.get_all(
                "Restaurant Object",
                filters={"name": ("in", table_names)},
                fields=["name", "type", "company", "room", "no_of_seats"],
                limit_page_length=len(table_names),
            )
        }
        if len(contexts) != len(table_names):
            frappe.throw(_("Seleccione únicamente mesas existentes"))

        primary_rows = []
        capacity = 0
        for row in rows:
            context = contexts.get(row.restaurant_table)
            if context.type != "Table" or context.company != self.company:
                frappe.throw(
                    _("La mesa {0} no pertenece a la compañía de la reserva").format(
                        row.restaurant_table
                    )
                )
            row.room = context.room
            row.capacity = cint(context.no_of_seats)
            capacity += row.capacity
            if cint(row.is_primary):
                primary_rows.append(row)

        if len(rows) == 1 and not primary_rows:
            rows[0].is_primary = 1
            primary_rows = [rows[0]]
        if len(primary_rows) != 1:
            frappe.throw(_("Seleccione exactamente una mesa principal"))

        if not cint(settings.get("allow_reservation_capacity_override")) and cint(
            self.guest_count
        ) > capacity:
            frappe.throw(
                _("La capacidad de las mesas ({0}) es menor a los {1} comensales").format(
                    capacity, self.guest_count
                )
            )

        if self.status in BLOCKING_STATUSES:
            self._lock_tables(table_names)
            self._validate_conflicts(table_names, settings)

    @staticmethod
    def _lock_tables(table_names):
        if not table_names:
            return
        placeholders = ", ".join(["%s"] * len(table_names))
        frappe.db.sql(
            "SELECT name FROM `tabRestaurant Object` "
            f"WHERE name IN ({placeholders}) ORDER BY name FOR UPDATE",
            tuple(sorted(table_names)),
        )

    def _validate_conflicts(self, table_names, settings):
        buffer_minutes = cint(settings.get("reservation_preparation_minutes")) + cint(
            settings.get("reservation_cleanup_minutes")
        )
        block_start = add_to_date(
            get_datetime(self.reservation_from), minutes=-buffer_minutes
        )
        block_end = add_to_date(
            get_datetime(self.reservation_to), minutes=buffer_minutes
        )
        placeholders = ", ".join(["%s"] * len(table_names))
        status_placeholders = ", ".join(["%s"] * len(BLOCKING_STATUSES))
        conflicts = frappe.db.sql(
            "SELECT r.name, rt.restaurant_table, ro.description AS table_description, "
            "r.reservation_from, r.reservation_to "
            "FROM `tabRestaurant Reservation` r "
            "INNER JOIN `tabRestaurant Reservation Table` rt ON rt.parent = r.name "
            "INNER JOIN `tabRestaurant Object` ro ON ro.name = rt.restaurant_table "
            "WHERE r.company = %s "
            f"AND r.status IN ({status_placeholders}) "
            "AND r.name != %s "
            f"AND rt.restaurant_table IN ({placeholders}) "
            "AND r.reservation_from < %s AND r.reservation_to > %s "
            "ORDER BY r.reservation_from LIMIT 1 FOR UPDATE",
            (
                self.company,
                *BLOCKING_STATUSES,
                self.name or "",
                *table_names,
                block_end,
                block_start,
            ),
            as_dict=True,
        )
        if conflicts:
            conflict = conflicts[0]
            frappe.throw(
                _("La mesa {0} ya está reservada en {1}, de {2} a {3}").format(
                    conflict.table_description or conflict.restaurant_table,
                    conflict.name,
                    conflict.reservation_from,
                    conflict.reservation_to,
                )
            )

    def _check_action_permission(self):
        self.check_permission("write")
        if frappe.session.user != "Administrator" and not ACTION_ROLES.intersection(
            frappe.get_roles()
        ):
            frappe.throw(_("No tiene permiso para operar reservas"), frappe.PermissionError)

    def _transition(self, target, timestamp_field, user_field, reason=None):
        self._check_action_permission()
        frappe.db.sql(
            "SELECT name FROM `tabRestaurant Reservation` WHERE name = %s FOR UPDATE",
            self.name,
        )
        self.reload()
        if target not in ALLOWED_TRANSITIONS.get(self.status, set()):
            frappe.throw(
                _("No se puede cambiar una reserva de {0} a {1}").format(
                    self.status, target
                )
            )
        if target == "Cancelled" and not (reason or "").strip():
            frappe.throw(_("Ingrese el motivo de cancelación"))

        self.flags.reservation_status_action = True
        self.status = target
        self.set(timestamp_field, now_datetime())
        self.set(user_field, frappe.session.user)
        if target == "Cancelled":
            self.cancellation_reason = reason.strip()
        self.save()
        return self.as_dict()

    @frappe.whitelist()
    def confirm_reservation(self):
        return self._transition("Confirmed", "confirmed_at", "confirmed_by")

    @frappe.whitelist()
    def mark_arrived(self):
        return self._transition("Arrived", "arrived_at", "arrived_by")

    @frappe.whitelist()
    def cancel_reservation(self, reason=None):
        return self._transition(
            "Cancelled", "cancelled_at", "cancelled_by", reason=reason
        )

    @frappe.whitelist()
    def mark_no_show(self):
        return self._transition("No Show", "no_show_at", "no_show_by")

    @frappe.whitelist()
    def seat_and_open_order(self):
        self._check_action_permission()
        frappe.db.sql(
            "SELECT name FROM `tabRestaurant Reservation` WHERE name = %s FOR UPDATE",
            self.name,
        )
        self.reload()
        if self.table_order:
            return {"table_order": self.table_order, "created": False}
        if self.status not in {"Confirmed", "Arrived"}:
            frappe.throw(_("Solo una reserva confirmada o llegada puede ser sentada"))

        settings = self._get_settings()
        self._validate_tables(settings)
        primary = next(
            (row for row in self.reservation_tables if cint(row.is_primary)), None
        )
        if not primary:
            frappe.throw(_("Seleccione la mesa principal"))

        reserved_tables = [row.restaurant_table for row in self.reservation_tables]
        active_order = frappe.db.get_value(
            "Table Order",
            {
                "table": ("in", reserved_tables),
                "company": self.company,
                "status": "Attending",
            },
            "name",
        )
        if active_order:
            frappe.throw(
                _("La mesa principal ya tiene la orden activa {0}").format(active_order)
            )

        table = frappe.get_doc("Restaurant Object", primary.restaurant_table)
        response = table.add_order(reservation=self.name)
        order_name = (
            response.get("data", {}).get("order", {}).get("data", {}).get("name")
        )
        if not order_name:
            frappe.throw(_("No se pudo crear la orden de la reserva"))

        order = frappe.get_doc("Table Order", order_name)
        order.reservation = self.name
        order.guest_count = self.guest_count
        customer = self.customer or settings.get("reservation_default_customer")
        if customer:
            order.customer = customer
        if self.assigned_waiter:
            order.cambio_mozo = self.assigned_waiter
        order.save()

        self.flags.reservation_status_action = True
        self.status = "Seated"
        self.table_order = order.name
        self.seated_at = now_datetime()
        self.seated_by = frappe.session.user
        self.save()
        return {"table_order": order.name, "created": True}

    def publish_update(self):
        table_names = {
            row.restaurant_table
            for row in self.get("reservation_tables") or []
            if row.restaurant_table
        }
        previous = self.get_doc_before_save()
        if previous:
            table_names.update(
                row.restaurant_table
                for row in previous.get("reservation_tables") or []
                if row.restaurant_table
            )
        table_names = sorted(table_names)
        frappe.publish_realtime(
            "restaurant_reservation_update",
            {
                "name": self.name,
                "company": self.company,
                "status": self.status,
                "tables": table_names,
            },
            after_commit=True,
        )
        for table_name in table_names:
            if frappe.db.exists("Restaurant Object", table_name):
                frappe.get_doc("Restaurant Object", table_name).synchronize()


def complete_reservation_for_order(doc, method=None):
    if doc.status != "Invoiced" or not doc.get("reservation"):
        return
    reservation = frappe.db.get_value(
        "Restaurant Reservation",
        doc.reservation,
        ["name", "status", "table_order"],
        as_dict=True,
    )
    if not reservation or reservation.status == "Completed":
        return
    if reservation.table_order and reservation.table_order != doc.name:
        frappe.throw(_("La reserva ya está vinculada a otra orden"))
    frappe.db.set_value(
        "Restaurant Reservation",
        reservation.name,
        {
            "status": "Completed",
            "table_order": doc.name,
            "completed_at": now_datetime(),
            "completed_by": frappe.session.user,
        },
        update_modified=True,
    )
    frappe.get_doc(
        "Restaurant Reservation", reservation.name
    ).publish_update()


def mark_expired_reservations_no_show():
    if not frappe.db.exists("DocType", "Restaurant Reservation"):
        return
    now = now_datetime()
    reservations = frappe.get_all(
        "Restaurant Reservation",
        filters={"status": ("in", ["Pending", "Confirmed"])},
        fields=["name", "company", "reservation_from"],
        limit_page_length=0,
    )
    for row in reservations:
        settings = get_restaurant_settings(company=row.company, required=False)
        if not settings or not cint(settings.get("reservation_auto_no_show")):
            continue
        grace = cint(settings.get("reservation_arrival_grace_minutes") or 0)
        expires_at = add_to_date(get_datetime(row.reservation_from), minutes=grace)
        if expires_at >= now:
            continue
        frappe.db.set_value(
            "Restaurant Reservation",
            row.name,
            {
                "status": "No Show",
                "no_show_at": now,
                "no_show_by": "Administrator",
            },
            update_modified=True,
        )
        frappe.get_doc("Restaurant Reservation", row.name).publish_update()


def get_table_reservation_summary(table_name, company, reference_time=None):
    if not frappe.db.exists("DocType", "Restaurant Reservation"):
        return None
    reference_time = get_datetime(reference_time) if reference_time else now_datetime()
    rows = frappe.db.sql(
        "SELECT r.name, r.status, r.guest_name, r.guest_count, "
        "r.reservation_from, r.reservation_to "
        "FROM `tabRestaurant Reservation` r "
        "INNER JOIN `tabRestaurant Reservation Table` rt ON rt.parent = r.name "
        "WHERE r.company = %s AND rt.restaurant_table = %s "
        "AND r.status IN ('Pending', 'Confirmed', 'Arrived', 'Seated') "
        "AND r.reservation_to >= %s "
        "ORDER BY r.reservation_from LIMIT 1",
        (company, table_name, reference_time),
        as_dict=True,
    )
    return rows[0] if rows else None


def validate_table_available_for_order(table_name, company, reservation=None):
    """Prevent walk-in orders from taking a table in its active reservation window."""
    settings = get_restaurant_settings(company=company)
    if not cint(settings.get("enable_reservations")):
        return
    now = now_datetime()
    window_start = add_to_date(
        now, minutes=-cint(settings.get("reservation_cleanup_minutes"))
    )
    window_end = add_to_date(
        now, minutes=cint(settings.get("reservation_preparation_minutes"))
    )
    rows = frappe.db.sql(
        "SELECT r.name, r.guest_name FROM `tabRestaurant Reservation` r "
        "INNER JOIN `tabRestaurant Reservation Table` rt ON rt.parent = r.name "
        "WHERE r.company = %s AND rt.restaurant_table = %s "
        "AND r.status IN ('Confirmed', 'Arrived', 'Seated') "
        "AND r.name != %s "
        "AND (r.status = 'Seated' OR "
        "(r.reservation_from <= %s AND r.reservation_to >= %s)) "
        "ORDER BY r.reservation_from LIMIT 1 FOR UPDATE",
        (company, table_name, reservation or "", window_end, window_start),
        as_dict=True,
    )
    if rows:
        frappe.throw(
            _("La mesa está bloqueada por la reserva {0} — {1}").format(
                rows[0].name,
                rows[0].guest_name,
            )
        )
