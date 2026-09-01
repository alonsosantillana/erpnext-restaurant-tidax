# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import hashlib
import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt, today
from erpnext.stock.get_item_details import get_price_list_rate_for
from erpnext.setup.utils import get_exchange_rate

from restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage import RestaurantManage
from restaurant_management.restaurant_management.doctype.order_entry_item.order_entry_item import (
    preparation_targets,
)
from restaurant_management.restaurant_management.doctype.restaurant_tip.restaurant_tip import (
    create_tip_record,
    post_tip_collection,
    validate_tip_request,
)
from restaurant_management.restaurant_management.company_settings import (
    get_restaurant_settings,
)
status_attending = "Attending"

VOUCHER_CONFIG = {
    ("Boleta", "Electrónica"): {
        "series_field": "serie_boleta",
        "document_code": "03",
        "document_label": "Boleta de Venta",
        "identity_code": "1",
        "identity_label": "DOCUMENTO NACIONAL DE IDENTIDAD (DNI)",
        "identity_length": 8,
    },
    ("Boleta", "Manual"): {
        "series_field": "serie_boleta_m",
        "document_code": "03",
        "document_label": "Boleta de Venta",
        "identity_code": "1",
        "identity_label": "DOCUMENTO NACIONAL DE IDENTIDAD (DNI)",
        "identity_length": 8,
    },
    ("Factura", "Electrónica"): {
        "series_field": "serie_factura",
        "document_code": "01",
        "document_label": "Factura",
        "identity_code": "6",
        "identity_label": "REGISTRO ÚNICO DE CONTRIBUYENTES",
        "identity_length": 11,
    },
    ("Factura", "Manual"): {
        "series_field": "serie_factura_m",
        "document_code": "01",
        "document_label": "Factura",
        "identity_code": "6",
        "identity_label": "REGISTRO ÚNICO DE CONTRIBUYENTES",
        "identity_length": 11,
    },
}


def get_voucher_config(voucher_type, emission_mode):
    voucher_type = (voucher_type or "").strip()
    emission_mode = (emission_mode or "").strip()
    config = VOUCHER_CONFIG.get((voucher_type, emission_mode))

    if not config:
        frappe.throw(
            _("Seleccione un tipo de comprobante y modo de emisión válidos"),
            frappe.ValidationError,
        )

    return config


def get_customer_identity(customer, config):
    identity = frappe.db.get_value(
        "Customer",
        customer,
        ["tax_id", "tipo_documento_identidad", "codigo_tipo_documento"],
        as_dict=True,
    )
    if not identity:
        frappe.throw(_("No se encontró el cliente seleccionado"))

    identity_code = str(identity.codigo_tipo_documento or "")
    if identity_code != config["identity_code"]:
        frappe.throw(
            _("El cliente debe tener {0} para emitir este comprobante").format(
                config["identity_label"]
            )
        )

    tax_id = "".join(
        character for character in str(identity.tax_id or "") if character.isdigit()
    )
    if len(tax_id) != config["identity_length"]:
        frappe.throw(
            _("El documento del cliente debe contener {0} dígitos").format(
                config["identity_length"]
            )
        )

    identity.tax_id = tax_id
    return identity


def apply_pos_tax_inclusion(invoice, tax_inclusive):
    """Make the POS Profile setting authoritative for every loaded tax row."""
    included_in_print_rate = cint(tax_inclusive)
    for tax in invoice.get("taxes"):
        tax.included_in_print_rate = included_in_print_rate


def apply_restaurant_pos_currency(invoice, pos_profile, selling_price_list, company):
    """Keep restaurant totals in the POS Profile currency, not the customer currency."""
    profile = frappe.db.get_value(
        "POS Profile",
        pos_profile,
        ["company", "currency"],
        as_dict=True,
    )
    if not profile or profile.company != company:
        frappe.throw(_("El perfil POS no corresponde a la empresa de la orden"))

    company_currency = frappe.get_cached_value("Company", company, "default_currency")
    price_list_currency = frappe.db.get_value(
        "Price List", selling_price_list, "currency"
    )
    transaction_currency = profile.currency or price_list_currency or company_currency

    if price_list_currency and price_list_currency != transaction_currency:
        frappe.throw(
            _("La moneda de la lista de precios debe coincidir con la moneda del perfil POS")
        )

    conversion_rate = get_exchange_rate(
        transaction_currency,
        company_currency,
        today(),
        "for_selling",
    )
    if not conversion_rate:
        frappe.throw(
            _("No existe un tipo de cambio para la moneda del perfil POS")
        )

    invoice.currency = transaction_currency
    invoice.conversion_rate = conversion_rate
    invoice.price_list_currency = price_list_currency or transaction_currency
    invoice.plc_conversion_rate = 1


def enforce_restaurant_pos_invoice_currency(invoice, method=None):
    """Reapply the restaurant POS currency after ERPNext party defaults run."""
    if not invoice.get("is_pos") or not invoice.get("pos_profile"):
        return invoice

    is_restaurant_profile = frappe.db.exists(
        "Restaurant Company Settings",
        {"company": invoice.company, "pos_profile": invoice.pos_profile},
    )
    if not is_restaurant_profile:
        return invoice

    apply_restaurant_pos_currency(
        invoice,
        invoice.pos_profile,
        invoice.selling_price_list,
        invoice.company,
    )
    tax_inclusive = frappe.db.get_value(
        "POS Profile", invoice.pos_profile, "posa_tax_inclusive"
    )
    apply_pos_tax_inclusion(invoice, tax_inclusive)
    invoice.calculate_taxes_and_totals()
    invoice.set_paid_amount()
    grand_total = flt(invoice.rounded_total or invoice.grand_total, 2)
    base_grand_total = flt(invoice.base_rounded_total or invoice.base_grand_total, 2)
    invoice.change_amount = flt(max(flt(invoice.paid_amount) - grand_total, 0), 2)
    invoice.base_change_amount = flt(
        max(flt(invoice.base_paid_amount) - base_grand_total, 0),
        2,
    )
    return invoice


def apply_delivery_fee_invoice_rate(invoice, delivery_fee_item):
    """Keep the user-entered delivery fee as the fiscal line price."""
    if not delivery_fee_item:
        return invoice

    for item in invoice.get("items"):
        if item.item_code != delivery_fee_item:
            continue
        item.price_list_rate = flt(item.rate)
        item.discount_percentage = 0
        item.discount_amount = 0
        item.margin_rate_or_amount = 0

    return invoice


PRE_ACCOUNT_REQUESTED = "Requested"
PRE_ACCOUNT_OUTDATED = "Outdated"


def _pre_account_number(value):
    return format(flt(value), ".6f")


def pre_account_signature(order):
    """Return a stable signature for content that changes a pre-account."""
    items = []
    for item in order.get("entry_items") or []:
        if flt(item.get("qty")) <= 0:
            continue
        items.append({
            "identifier": item.get("identifier") or "",
            "item_code": item.get("item_code") or "",
            "qty": _pre_account_number(item.get("qty")),
            "rate": _pre_account_number(item.get("rate")),
            "price_list_rate": _pre_account_number(item.get("price_list_rate")),
            "amount": _pre_account_number(item.get("amount")),
            "discount_percentage": _pre_account_number(item.get("discount_percentage")),
            "discount_amount": _pre_account_number(item.get("discount_amount")),
        })

    items.sort(key=lambda row: (row["identifier"], row["item_code"]))
    payload = {
        "items": items,
        "discount": _pre_account_number(order.get("discount")),
        "discount_global_percent": _pre_account_number(order.get("discount_global_percent")),
        "tax": _pre_account_number(order.get("tax")),
        "amount": _pre_account_number(order.get("amount")),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class TableOrder(Document):
    def validate(self):
        self.validate_service_context()
        self.set_default_customer()
        self.validate_global_discount()
        self.invalidate_pre_account_if_changed()

    def invalidate_pre_account_if_changed(self):
        if (
            self.is_new()
            or self.status != status_attending
            or self.pre_account_status != PRE_ACCOUNT_REQUESTED
            or not self.pre_account_signature
        ):
            return

        if self.pre_account_signature != pre_account_signature(self):
            self.pre_account_status = PRE_ACCOUNT_OUTDATED

    def mark_pre_account_requested(self):
        if not self.is_dine_in or self.status != status_attending:
            frappe.throw(_("Only an active dine-in order can request an account"))
        if not any(flt(item.qty) > 0 for item in self.entry_items):
            frappe.throw(_("The order has no dishes to print"))

        self.pre_account_status = PRE_ACCOUNT_REQUESTED
        self.pre_account_requested_at = frappe.utils.now_datetime()
        self.pre_account_requested_by = frappe.session.user
        self.pre_account_signature = pre_account_signature(self)
        self.save()
        return {
            "status": self.pre_account_status,
            "requested_at": self.pre_account_requested_at,
            "requested_by": self.pre_account_requested_by,
        }

    def validate_service_context(self):
        self.service_type = self.service_type or "Dine In"
        if self.service_type not in {"Dine In", "Delivery", "Pickup"}:
            frappe.throw(_("Select a valid service type"))

        profile_company = (
            frappe.db.get_value("POS Profile", self.pos_profile, "company")
            if self.pos_profile
            else None
        )
        if not self.company:
            self.company = profile_company
        if profile_company and self.company != profile_company:
            frappe.throw(_("POS Profile and order must belong to the same company"))

        if self.service_type == "Dine In":
            if not self.table:
                frappe.throw(_("Dine-in orders require a restaurant table"))
            table_context = frappe.db.get_value(
                "Restaurant Object",
                self.table,
                ["type", "company"],
                as_dict=True,
            )
            if not table_context or table_context.type != "Table":
                frappe.throw(_("Select a valid restaurant table"))
            if self.company and self.company != table_context.company:
                frappe.throw(
                    _("Restaurant table and order must belong to the same company")
                )
            self.company = table_context.company
        elif self.table:
            frappe.throw(_("Delivery and pickup orders cannot use a restaurant table"))

        if not self.company:
            frappe.throw(_("Company is required for a restaurant order"))

    @property
    def is_dine_in(self):
        return (self.service_type or "Dine In") == "Dine In"

    @property
    def context_label(self):
        if self.is_dine_in:
            return f"{self.room_description} ({self.table_description})"
        service_label = "DELIVERY" if self.service_type == "Delivery" else "PICKUP"
        customer_name = self.customer_name or self.customer or ""
        return f"{service_label} {self.short_name} | {customer_name}".strip()

    @staticmethod
    def item_process_status_data(item):
        from restaurant_management.restaurant_management.doctype.restaurant_object.restaurant_object import RestaurantObject

        status = RestaurantObject._status(item.status)
        return {
            "next_action_message": status["action_message"],
            "color": status["color"],
            "icon": status["icon"],
            "status_message": status["message"],
        }

    def on_update(self):
        previous = self.get_doc_before_save()
        if (
            previous
            and self.is_dine_in
            and (
                self.has_value_changed("pre_account_status")
                or self.has_value_changed("pre_account_requested_at")
            )
        ):
            self.synchronize(dict(action="PreAccount"))
        elif previous and (
            self.has_value_changed("discount")
            or self.has_value_changed("discount_global_percent")
        ):
            self.synchronize(dict(action="Update"))
        elif previous and self.has_value_changed("guest_count") and self.is_dine_in:
            self._table.synchronize()

    def validate_global_discount(self):
        discount = flt(self.discount)
        discount_percent = flt(self.discount_global_percent)
        order_amount = flt(self.amount)

        if discount < 0 or discount_percent < 0:
            frappe.throw(_("Global discount cannot be negative"))
        if discount_percent > 100:
            frappe.throw(_("Global discount percent cannot exceed 100"))
        if discount > 0 and discount_percent > 0:
            frappe.throw(_("Use either a discount amount or a discount percent, not both"))
        if discount > order_amount:
            frappe.throw(_("Global discount cannot exceed the order total"))

        discount_changed = self.is_new() or (
            self.has_value_changed("discount")
            or self.has_value_changed("discount_global_percent")
        )
        if discount_changed and (discount > 0 or discount_percent > 0):
            allow_discount_change = cint(
                frappe.db.get_value(
                    "POS Profile", self.pos_profile, "allow_discount_change"
                )
            )
            if not allow_discount_change:
                frappe.throw(_("The POS Profile does not allow changing discounts"))

        self.discount = discount
        self.discount_global_percent = discount_percent

    def set_default_customer(self):
        if self.customer:
            return

        self.customer = frappe.db.get_value('POS Profile', self.pos_profile, 'customer')

    @property
    def short_name(self):
        return self.name[8:]

    @property
    def items_count(self):
        return frappe.db.count("Order Entry Item", filters={
            "parenttype": "Table Order", "parent": self.name, "qty": (">", "0")
        })

    @property
    def products_not_ordered_count(self):
        return frappe.db.count("Order Entry Item", filters={
            "parenttype": "Table Order", "parent": self.name, "status": status_attending
        })

    @property
    def _table(self):
        return frappe.get_doc("Restaurant Object", self.table)

    def divide_template(self):
        items = self.items_list()
        divide_total = 0
        for item in items:
            item["divide_amount"] = flt(item["qty"]) * flt(item["rate"])
            divide_total += item["divide_amount"]

        return frappe.render_template(
            "restaurant_management/restaurant_management/doctype/table_order/divide_template.html", {
                "model": self,
                "items": items,
                "table": self.table,
                "divide_total": divide_total,
            })

    def get_restaurant(self):
        table = frappe.get_doc("Restaurant Object", self.table)
        return frappe.db.get_value('Restaurant', table._restaurant)

    def validate_divide_items(self, items):
        if not isinstance(items, dict) or not items:
            frappe.throw(_("Select at least one dish to divide"))

        entries = {
            item.identifier: item
            for item in self.entry_items
            if item.identifier and flt(item.qty) > 0
        }
        total_qty = sum(flt(item.qty) for item in entries.values())
        selected_qty = 0
        quantities = {}

        for identifier, selection in items.items():
            if identifier not in entries or not isinstance(selection, dict):
                frappe.throw(_("Invalid dish selected for division"))

            qty = flt(selection.get("qty"))
            available_qty = flt(entries[identifier].qty)
            if qty <= 0 or qty > available_qty:
                frappe.throw(
                    _("The quantity selected for {0} must be between 1 and {1}").format(
                        entries[identifier].item_name or entries[identifier].item_code,
                        available_qty,
                    )
                )

            quantities[identifier] = qty
            selected_qty += qty

        if selected_qty >= total_qty:
            frappe.throw(_("At least one dish must remain in the current account"))

        return quantities

    def divide(self, items, client):
        if not self.is_dine_in:
            frappe.throw(_("Only dine-in orders can be divided"))
        quantities = self.validate_divide_items(items)
        new_order = frappe.new_doc("Table Order")
        self.transfer_order_values(new_order)
        new_order.save()
        status = []

        for item in self.entry_items:
            divide_qty = quantities.get(item.identifier)

            if divide_qty is not None:
                rest = flt(item.qty) - divide_qty
                current_item = self.items_list(item.identifier)[0]
                current_item["qty"] = rest
                self.update_item(current_item, True, False)

                new_order.update_item(dict(
                    item_code=item.item_code,
                    qty=divide_qty,
                    rate=item.rate,
                    price_list_rate=item.price_list_rate,
                    item_tax_template=item.item_tax_template,
                    item_tax_rate=item.item_tax_rate,
                    discount_percentage=item.discount_percentage,
                    status=item.status,
                    identifier=item.identifier if rest == 0 else f"entry_{frappe.generate_hash(length=12)}",
                    notes=item.notes,
                    ordered_time=item.ordered_time,
                    ordered_nro=item.ordered_nro,
                    ordered_finish=item.ordered_finish,
                    processing_started_at=item.processing_started_at,
                    processing_started_by=item.processing_started_by,
                    completed_at=item.completed_at,
                    completed_by=item.completed_by,
                    waiting_time_minutes=item.waiting_time_minutes,
                    preparation_time_minutes=item.preparation_time_minutes,
                    total_time_minutes=item.total_time_minutes,
                    preparation_time_target=item.preparation_time_target,
                    preparation_time_source=item.preparation_time_source,
                    table_description=self.context_label,
                    has_batch_no=item.has_batch_no,
                    batch_no=item.batch_no,
                    has_serial_no=item.has_serial_no,
                    serial_no=item.serial_no,
                    unit_value=item.unit_value
                ))

            status.append(item.status)

        self.db_commit()
        new_order.aggregate()
        new_order.save()

        new_order.synchronize(dict(action="Add", client=client))
        self.synchronize(dict(action="Split", client=client, status=status))

        return dict(
            current_order=self.data(),
            new_order=new_order.data(),
        )

    @staticmethod
    def debug_data(data):
        frappe.publish_realtime("debug_data", data)

    @staticmethod
    def options_param(options, param):
        return None if options is None else (options[param] if param in options else None)

    def synchronize(self, options=None):
        action = self.options_param(options, "action") or "Update"
        items = self.options_param(options, "items")
        last_table = self.options_param(options, "last_table")
        status = self.options_param(options, "status")
        item_removed = self.options_param(options, "item_removed")

        event = dict(
            action=action,
            data=[] if action is None else self.data(items, last_table),
            client=self.options_param(options, "client"),
            item_removed=item_removed
        )
        frappe.publish_realtime("synchronize_order_data", event, after_commit=True)

        if self.is_dine_in:
            self._table.synchronize()
        else:
            fulfillment = frappe.db.get_value(
                "Restaurant Fulfillment",
                {"order": self.name},
                ["name", "fulfillment_type", "status"],
                as_dict=True,
            )
            if fulfillment:
                frappe.publish_realtime(
                    "restaurant_fulfillment_update",
                    {
                        "name": fulfillment.name,
                        "order": self.name,
                        "fulfillment_type": fulfillment.fulfillment_type,
                        "status": fulfillment.status,
                    },
                    after_commit=True,
                )

        if status is not None:
            RestaurantManage.production_center_notify(status)

        return event

    def make_invoice(
        self,
        mode_of_payment,
        customer=None,
        guest_count=0,
        voucher_type=None,
        emission_mode=None,
        tip_amount=0,
        tip_mode_of_payment=None,
    ):
        # Restaurant roles do not implicitly grant accounting permissions. The
        # effective ERPNext permission is authoritative and also supports users
        # configured without one of the obsolete Role Profile names.
        if not frappe.has_permission("POS Invoice", "create"):
            frappe.throw(
                _("No tiene permisos suficientes para generar el comprobante"),
                frappe.PermissionError,
            )

        if self.link_invoice:
            return frappe.throw(_("The order has been invoiced"))

        customer = str(customer or "").strip()
        voucher_type = str(voucher_type or "").strip()
        emission_mode = str(emission_mode or "").strip()
        guest_count = cint(guest_count)
        if not customer:
            frappe.throw(_("Seleccione un cliente"))
        if self.is_dine_in and guest_count <= 0:
            frappe.throw(_("La cantidad de comensales debe ser mayor que cero"))
        if not self.is_dine_in:
            guest_count = max(0, guest_count)

        tip_context = validate_tip_request(self, tip_amount, tip_mode_of_payment)

        voucher_config = get_voucher_config(voucher_type, emission_mode)
        customer_identity = get_customer_identity(customer, voucher_config)

        self.customer = customer
        self.guest_count = guest_count
        self.voucher_type = voucher_type
        self.emission_mode = emission_mode
        self.save()
        self.reload()

        entry_items = {
            item.identifier: item.as_dict() for item in self.entry_items
        }
        # print("MAKE INVOICE ----------------------->")
        # print(entry_items)
        if len(entry_items) == 0:
            frappe.throw(_("There is not Item in this Order"))

        invoice = self.get_invoice(entry_items, True)
        invoice.payments = []
        for mp in mode_of_payment:
            invoice.append('payments', dict(
                mode_of_payment=mp,
                amount=mode_of_payment[mp]
            ))

        # TIDAX: CASOS PRODUCTOS GRATIS
        total_dicount_lines = 0
        total_free = 0
        for it in self.entry_items:
            total_dicount_lines += (it.discount_amount * it.qty)
            total_free += (it.unit_value * it.qty)
            if(it.price_list_rate == 0):
                total_free += 1 * it.qty

        settings = get_restaurant_settings(order=self)
        series = settings.get(voucher_config["series_field"])
        if not series:
            frappe.throw(
                _("Configure la serie {0} en Restaurant Company Settings").format(
                    voucher_config["series_field"]
                )
            )

        invoice.naming_series = series
        invoice.codigo_comprobante = voucher_config["document_code"]
        invoice.tipo_comprobante = voucher_config["document_label"]
        invoice.comprobante_electronico_manual = emission_mode
        invoice.codigo_tipo_documento = voucher_config["identity_code"]
        invoice.tipo_documento_identidad = customer_identity.tipo_documento_identidad
        invoice.codigo_transaccion_sunat = "1"
        invoice.tipo_transaccion_sunat = "VENTA INTERNA"
        invoice.condicion_pago = "CONTADO"
        invoice.tax_id = customer_identity.tax_id
        invoice.total_amount_discount_lines = total_dicount_lines

        if self.discount > 0 and self.discount < self.amount:
            invoice.discount_amount = self.discount
        if self.discount_global_percent > 0 and self.discount_global_percent < 100:
            invoice.additional_discount_percentage = self.discount_global_percent
        if self.discount_global_percent == 100 or self.discount == self.amount:
            invoice.additional_discount_percentage = 100

        if total_free > 0:
            invoice.total_amount_free = total_free
        elif self.discount_global_percent >= 100 or self.discount >= self.amount:
            invoice.total_amount_free = self.amount
            invoice.is_free_global = 1

        invoice.table_description = self.context_label
        if not self.is_dine_in:
            fulfillment = frappe.db.get_value(
                "Restaurant Fulfillment",
                {"order": self.name},
                ["address", "address_display_snapshot", "contact_phone"],
                as_dict=True,
            )
            if fulfillment:
                invoice.customer_address = fulfillment.address
                invoice.shipping_address_name = fulfillment.address
                invoice.address_display = fulfillment.address_display_snapshot
                invoice.contact_mobile = fulfillment.contact_phone
        invoice.validate()
        enforce_restaurant_pos_invoice_currency(invoice)
        invoice_total = flt(invoice.rounded_total or invoice.grand_total, 2)
        payment_total = flt(
            sum(flt(payment.amount) for payment in invoice.payments),
            2,
        )
        if abs(payment_total - invoice_total) > 0.005:
            frappe.throw(
                _("Los medios de pago deben sumar {0}").format(invoice_total)
            )
        invoice.save()
        tip = create_tip_record(self, invoice, tip_context)
        invoice.submit()
        if tip:
            tip = post_tip_collection(tip)

        self.status = "Invoiced"
        self.link_invoice = invoice.name

        # TIDAX
        self.total_amount_discount_lines = total_dicount_lines

        self.save()
        self.submit()

        if not self.is_dine_in:
            fulfillment = frappe.db.get_value(
                "Restaurant Fulfillment",
                {"order": self.name},
                ["name", "fulfillment_type", "status"],
                as_dict=True,
            )
            if fulfillment:
                frappe.db.set_value(
                    "Restaurant Fulfillment",
                    fulfillment.name,
                    "payment_status",
                    "Paid",
                )
                frappe.publish_realtime(
                    "restaurant_fulfillment_update",
                    {
                        "name": fulfillment.name,
                        "order": self.name,
                        "fulfillment_type": fulfillment.fulfillment_type,
                        "status": fulfillment.status,
                    },
                    after_commit=True,
                )

        frappe.msgprint(_('Invoice Created'), indicator='green', alert=True)

        self.synchronize(dict(action="Invoiced", status=["Invoiced"]))

        return dict(
            status=True,
            invoice_name=invoice.name,
            tip_name=tip.name if tip else None,
            tip_amount=tip.amount if tip else 0,
            tip_status=tip.status if tip else None,
        )

    def transfer(self, table, client):
        if not self.is_dine_in:
            frappe.throw(_("Only dine-in orders can be transferred to another table"))
        last_table = self._table
        new_table = frappe.get_doc("Restaurant Object", table)
        if new_table.type != "Table":
            frappe.throw(_("Select a valid restaurant table"))
        if new_table.company != self.company:
            frappe.throw(
                _("Orders cannot be transferred between companies")
            )

        # last_table.validate_user()
        last_table_name = self.table
        new_table.validate_transaction(self.owner)

        self.table = table

        self.save()

        for i in self.entry_items:
            table_description = self.context_label
            frappe.db.set_value("Order Entry Item", {"identifier": i.identifier}, "table_description",
                                table_description)

        self.reload()
        transfer_event = self.synchronize(dict(
            action="Transfer",
            client=client,
            last_table=last_table_name
        ))

        last_table.synchronize()
        return dict(
            transfer_event=transfer_event,
            source_table=last_table.get_data(),
            destination_table=new_table.get_data(),
        )

    def transfer_order_values(self, to_doc):
        # print("TRANSFER ORDER VALUES-------------------->")
        # print(self)
        to_doc.company = self.company
        to_doc.is_pos = 1
        to_doc.customer = self.customer
        to_doc.title = self.customer
        to_doc.taxes_and_charges = self.taxes_and_charges
        to_doc.selling_price_list = self.selling_price_list
        to_doc.pos_profile = self.pos_profile
        to_doc.table = self.table
        if to_doc.doctype == "Table Order":
            to_doc.service_type = self.service_type

    def get_invoice(self, entry_items=None, make=False):
        invoice = frappe.new_doc("POS Invoice")
        self.transfer_order_values(invoice)

        invoice.items = []
        invoice.taxes = []
        taxes = {}
        
        for i in entry_items:
            item = entry_items[i]
            # print("GET INVOICE -------------------->")
            # print(item)
            if item["qty"] > 0:
                price_list_rate = flt(item.get("price_list_rate"))
                rate = flt(item.get("rate"))
                discount_percentage = flt(item.get("discount_percentage"))
                unit_value = flt(item.get("unit_value"))

                if price_list_rate <= 0:
                    price_list_rate = flt(
                        get_price_list_rate_for(
                            frappe._dict(
                                price_list=self.selling_price_list,
                                customer=self.customer,
                                uom=item.get("stock_uom"),
                                stock_uom=item.get("stock_uom"),
                                transaction_date=today(),
                                qty=flt(item.get("qty")),
                                conversion_factor=1,
                                ignore_party=True,
                            ),
                            item.get("item_code"),
                        )
                    )
                    if price_list_rate <= 0:
                        frappe.throw(
                            _("Item {0} has no price configured in Price List {1}").format(
                                frappe.bold(item.get("item_name") or item.get("item_code")),
                                frappe.bold(self.selling_price_list),
                            )
                        )

                    item["price_list_rate"] = price_list_rate
                    rate = price_list_rate * (1 - discount_percentage / 100)
                    item["rate"] = rate

                margin_rate_or_amount = (rate - price_list_rate)
                invoice.append('items', dict(
                    identifier=item["identifier"],
                    item_code=item["item_code"],
                    qty=item["qty"],
                    price_list_rate=price_list_rate,
                    rate=rate,
                    discount_percentage=discount_percentage,

                    item_tax_template=item["item_tax_template"] if "item_tax_template" in item else None,
                    item_tax_rate=item["item_tax_rate"] if "item_tax_rate" in item else None,

                    margin_type="Amount",
                    margin_rate_or_amount=0 if margin_rate_or_amount < 0 else margin_rate_or_amount,

                    has_serial_no=item["has_serial_no"],
                    serial_no=item["serial_no"],
                    
                    has_batch_no=item["has_batch_no"],
                    batch_no=item["batch_no"],

                    conversion_factor=1,
                    unit_value=0 if unit_value <= 0 else unit_value,
                ))
                

                if "item_tax_rate" in item:
                    if not item["item_tax_rate"] in taxes:
                        taxes[item["item_tax_rate"]] = item["item_tax_rate"]

        in_invoice_taxes = [t for t in invoice.get("taxes")]

        for tax in taxes:
            if tax is not None:
                for t in json.loads(tax):
                    in_invoice_taxes.append(t)
        
        included_in_print_rate = frappe.db.get_value("POS Profile", self.pos_profile, "posa_tax_inclusive")
        cost_center = frappe.db.get_value(
            "POS Profile", self.pos_profile, "cost_center")

        invoice.cost_center = cost_center

        for t in set(in_invoice_taxes):
            invoice.append('taxes', {
                "charge_type": "On Net Total",# + apply_discount_on,
                "account_head": t,
                "rate": 0, 
                "description": t,
                "included_in_print_rate": included_in_print_rate
            })
            
        invoice.run_method("set_missing_values")
        if self.service_type == "Delivery":
            settings = get_restaurant_settings(order=self)
            apply_delivery_fee_invoice_rate(invoice, settings.delivery_fee_item)
        apply_restaurant_pos_currency(
            invoice,
            self.pos_profile,
            self.selling_price_list,
            self.company,
        )
        apply_pos_tax_inclusion(invoice, included_in_print_rate)
        invoice.run_method("calculate_taxes_and_totals")

        ##To validate the invoice
        invoice.payments = []
        invoice.append('payments', dict(
            mode_of_payment="cash",
            amount=invoice.grand_total
        ))
        invoice._action = "submit"
        invoice.validate()
        enforce_restaurant_pos_invoice_currency(invoice)
        ##To validate the invoice

        return invoice

    def set_queue_items(self, all_items):
        from restaurant_management.restaurant_management.restaurant_manage import check_exceptions
        check_exceptions(
            dict(name="Table Order", short_name="order", action="write", data=self),
            "You cannot modify an order from another User"
        )
        self.calculate_order(all_items)
        self.synchronize(dict(action="queue"))

    def add_delivery_fee_item(self, item_code, rate):
        if self.service_type != "Delivery":
            frappe.throw(_("Delivery fees only apply to delivery orders"))

        rate = flt(rate)
        if rate <= 0:
            frappe.throw(_("Delivery fee must be greater than zero"))
        item_doc = frappe.get_cached_doc("Item", item_code)
        if item_doc.disabled or not item_doc.is_sales_item:
            frappe.throw(_("Configure an enabled sales Item for the delivery fee"))
        if item_doc.is_stock_item:
            frappe.throw(_("The delivery fee Item must be non-stock"))

        existing = [item for item in self.entry_items if item.item_code == item_code]
        if len(existing) > 1:
            frappe.throw(_("The order contains more than one delivery fee line"))
        identifier = (
            existing[0].identifier
            if existing
            else f"delivery_fee_{frappe.generate_hash(length=10)}"
        )
        timestamp = frappe.utils.now_datetime()
        entry = {
            "identifier": identifier,
            "item_code": item_code,
            "qty": 1,
            "rate": rate,
            "price_list_rate": rate,
            "discount_percentage": 0,
            "discount_amount": 0,
            "item_tax_template": None,
            "item_tax_rate": "{}",
            "status": "Completed",
            "notes": _("Delivery fee"),
            "ordered_time": timestamp,
            "ordered_nro": 0,
            "ordered_finish": 0,
            "processing_started_at": timestamp,
            "processing_started_by": frappe.session.user,
            "completed_at": timestamp,
            "completed_by": frappe.session.user,
            "waiting_time_minutes": 0,
            "preparation_time_minutes": 0,
            "total_time_minutes": 0,
            "preparation_time_target": 0,
            "preparation_time_source": None,
            "has_batch_no": 0,
            "batch_no": None,
            "has_serial_no": 0,
            "serial_no": None,
            "unit_value": 0,
        }
        action = self.update_item(entry, unrestricted=True)
        if action == "db_commit":
            self.reload()
        self.aggregate()
        return identifier

    def _validate_delivery_fee_item_change(self, item_code, unrestricted=False):
        if unrestricted or self.is_dine_in:
            return
        settings = get_restaurant_settings(order=self)
        fee_item = settings.delivery_fee_item
        if fee_item and item_code == fee_item:
            frappe.throw(_("Change the delivery fee from the delivery details"))

    def push_item(self, item):
        if self.customer is None:
            frappe.throw(_("Please set a Customer"))
            
        from restaurant_management.restaurant_management.restaurant_manage import check_exceptions
        check_exceptions(
            dict(name="Table Order", short_name="order", action="write", data=self),
            "You cannot modify an order from another User"
        )
        action = self.update_item(item)

        if action == "db_commit":
            self.db_commit()
        else:
            self.aggregate()

        return self.synchronize(dict(item=item["identifier"]))

    def increment_item(self, identifier, delta=1):
        if self.customer is None:
            frappe.throw(_("Please set a Customer"))

        delta = cint(delta)
        if delta < 1 or delta > 100:
            frappe.throw(_("The quantity increment must be between 1 and 100"))

        from restaurant_management.restaurant_management.restaurant_manage import check_exceptions
        check_exceptions(
            dict(name="Table Order", short_name="order", action="write", data=self),
            "You cannot modify an order from another User"
        )

        frappe.db.sql(
            "SELECT name FROM `tabTable Order` WHERE name = %s FOR UPDATE",
            (self.name,),
        )
        self.reload()
        items = self.items_list(identifier)
        if len(items) != 1 or items[0].get("status") != status_attending:
            frappe.throw(_("The selected dish can no longer be increased"))

        item = items[0]
        item["qty"] = flt(item.get("qty")) + delta
        item["status"] = status_attending
        action = self.update_item(item)
        if action == "db_commit":
            self.db_commit()
        else:
            self.aggregate()

        return self.synchronize(dict(item=identifier))

    def delete_item(self, item, unrestricted=False, synchronize=True):
        item_code = frappe.db.get_value(
            "Order Entry Item", {"identifier": item}, "item_code"
        )
        self._validate_delivery_fee_item_change(item_code, unrestricted)
        if not unrestricted:
            from restaurant_management.restaurant_management.restaurant_manage import check_exceptions
            check_exceptions(
                dict(name="Table Order", short_name="order", action="write", data=self),
                "You cannot modify an order from another User"
            )

        status = frappe.db.get_value("Order Entry Item", {'identifier': item}, "status")
        frappe.db.delete('Order Entry Item', {'identifier': item})
        self.db_commit()

        if synchronize and frappe.db.count("Order Entry Item", {"identifier": item}) == 0:
            return self.synchronize(
                dict(action='queue', item_removed=item, status=[status])
            )

    def db_commit(self):
        frappe.db.commit()
        self.reload()
        self.aggregate()

    def aggregate(self):
        entry_items = {
            item.identifier: item.as_dict()
            for item in self.entry_items
            if flt(item.qty) > 0
        }
        if entry_items:
            invoice = self.get_invoice(entry_items)
            self.tax = invoice.base_total_taxes_and_charges
            self.amount = invoice.grand_total
        else:
            self.tax = 0
            self.amount = 0
        self.save()

    def update_item(self, entry, unrestricted=False, synchronize_on_delete=True):
        self._validate_delivery_fee_item_change(entry.get("item_code"), unrestricted)
        if entry["qty"] == 0:
            self.delete_item(entry["identifier"], unrestricted, synchronize_on_delete)
            return "db_commit"
        else:
            invoice = self.get_invoice({entry["identifier"]: entry})
            item = invoice.items[0]
            # TIDAX : Obtencion de cocinas dependiendo del grupo de productos
            PrCeGr = frappe.db.sql(f"""SELECT ro.description FROM `tabRestaurant Object` as ro inner join
                                    `tabProduction Center Group` as pcg on ro.name = pcg.parent and ro.type = 'Production Center' and item_group = '{item.item_group}' 
                                    order by item_group asc;""", as_dict=True)
            
            # # TIDAX : Obtencion de ordered_nro
            # identifier = entry["identifier"]
            # # Obtener parent como una lista de resultados
            # parent_result = frappe.db.sql(f"""SELECT DISTINCT(oei.parent) as parent FROM `tabOrder Entry Item` as oei 
            #                   WHERE oei.identifier = '{identifier}';""", as_dict=True)
            # # Verificar si se obtuvieron resultados antes de acceder a parent
            # if parent_result:
            #     parent = parent_result[0]["parent"]

            #     # Obtener el valor máximo de ordered_nro para el parent obtenido
            #     nro_orden_result = frappe.db.sql(f"""SELECT MAX(oei.ordered_nro) as max_parent 
            #                                     FROM `tabOrder Entry Item` as oei 
            #                                     WHERE oei.parent = '{parent}';""", as_dict=True)

            #     # Verificar si se obtuvieron resultados antes de imprimir
            #     if nro_orden_result and nro_orden_result[0]["max_parent"] is not None:
            #         print(nro_orden_result[0]["max_parent"])
            #     else:
            #         print("No se encontraron resultados para ordered_nro.")
            # else:
            #     print("No se encontraron resultados para el identificador proporcionado.")
            #     nro_orden_result = [{"max_parent": 1}]
            #     print(nro_orden_result[0]["max_parent"])


            centro_pro = ""

            for pt in PrCeGr:
                centro_pro += pt.description + "| "

            entry_status = (
                status_attending
                if entry.get("status") in ["Pending", "", None]
                else entry.get("status")
            )
            is_unsent = entry_status == status_attending
            data = dict(
                item_code=item.item_code,
                qty=item.qty,
                rate=item.rate,
                price_list_rate=item.price_list_rate,
                item_tax_template=item.item_tax_template,
                item_tax_rate=item.item_tax_rate,
                tax_amount=invoice.base_total_taxes_and_charges,
                amount=invoice.grand_total,
                discount_percentage=item.discount_percentage,
                discount_amount=item.discount_amount,
                status=entry_status,
                identifier=entry["identifier"],
                notes=entry["notes"],
                table_description=self.context_label,
                ordered_time=None if is_unsent else entry.get("ordered_time"),
                ordered_nro=0 if is_unsent else (entry.get("ordered_nro") or 1),
                ordered_finish=entry.get("ordered_finish") or 0,
                processing_started_at=entry.get("processing_started_at"),
                processing_started_by=entry.get("processing_started_by"),
                completed_at=entry.get("completed_at"),
                completed_by=entry.get("completed_by"),
                waiting_time_minutes=entry.get("waiting_time_minutes"),
                preparation_time_minutes=entry.get("preparation_time_minutes"),
                total_time_minutes=entry.get("total_time_minutes"),
                preparation_time_target=entry.get("preparation_time_target"),
                preparation_time_source=entry.get("preparation_time_source"),
                has_batch_no=entry["has_batch_no"],
                batch_no=entry["batch_no"],
                has_serial_no=entry["has_serial_no"],
                serial_no=entry["serial_no"],
                # TIDAX : Adicion de cocinas y caso descuento es 100%
                item_pt = centro_pro,
                unit_value = item.price_list_rate if item.discount_percentage == 100 else 0
            )

            self.validate()

            if frappe.db.count("Order Entry Item", {"identifier": entry["identifier"]}) == 0:
                self.append('entry_items', data)
                return "aggregate"
            else:
                frappe.db.set_value(
                    "Order Entry Item",
                    {"identifier": entry["identifier"]},
                    data,
                )
                return "db_commit"

    def calculate_order(self, items):
        entry_items = {item["identifier"]: item for item in items}
        invoice = self.get_invoice(entry_items)

        self.entry_items = []
        for item in invoice.items:
            entry_item = entry_items[item.serial_no] if item.serial_no in entry_items else None
            entry_status = (
                status_attending
                if entry_item.get("status") in ["Pending", "", None]
                else entry_item.get("status")
            )
            is_unsent = entry_status == status_attending

            self.append('entry_items', dict(
                item_code=item.item_code,
                qty=item.qty,
                rate=item.rate,
                price_list_rate=item.price_list_rate,
                item_tax_template=item.item_tax_template,
                item_tax_rate=item.item_tax_rate,
                amount=item.amount,
                discount_percentage=item.discount_percentage,
                discount_amount=item.discount_amount,
                status=entry_status,
                identifier=entry_item["identifier"],
                notes=entry_item["notes"],
                ordered_time=None if is_unsent else entry_item.get("ordered_time"),
                processing_started_at=entry_item.get("processing_started_at"),
                processing_started_by=entry_item.get("processing_started_by"),
                completed_at=entry_item.get("completed_at"),
                completed_by=entry_item.get("completed_by"),
                waiting_time_minutes=entry_item.get("waiting_time_minutes"),
                preparation_time_minutes=entry_item.get("preparation_time_minutes"),
                total_time_minutes=entry_item.get("total_time_minutes"),
                preparation_time_target=entry_item.get("preparation_time_target"),
                preparation_time_source=entry_item.get("preparation_time_source"),
                table_description=self.context_label,
                has_batch_no=entry_item["has_batch_no"],
                batch_no=entry_item["batch_no"],
                has_serial_no=entry_item["has_serial_no"],
                serial_no=entry_item["serial_no"],
                # TIDAX : Adicion
                unit_value=entry_item["unit_value"],
                ordered_finish=entry_item["ordered_finish"],
                ordered_nro=0 if is_unsent else (entry_item.get("ordered_nro") or 1)
            ))
            item.serial_no = None

        self.tax = invoice.base_total_taxes_and_charges
        self.amount = invoice.grand_total
        self.save()

    @property
    def identifier(self):
        return self.name

    def data(self, items=None, last_table=None):
        return dict(
            order=self.short_data(last_table),
            items=self.items_list() if items is None else items
        )

    def short_data(self, last_table=None):
        return dict(
            data=dict(
                last_table=last_table,
                table=self.table,
                customer=self.customer,
                name=self.name,
                status=self.status,
                short_name=self.short_name,
                items_count=self.items_count,
                attending_status=status_attending,
                products_not_ordered=self.products_not_ordered_count,
                tax=self.tax,
                amount=self.amount,
                discount=self.discount,
                discount_global_percent=self.discount_global_percent,
                owner=self.owner,
                guest_count=self.guest_count,
                service_type=self.service_type or "Dine In",
                customer_name=self.customer_name,
                context_label=self.context_label,
                pre_account_status=self.pre_account_status,
                pre_account_requested_at=self.pre_account_requested_at,
                fulfillment=frappe.db.get_value(
                    "Restaurant Fulfillment",
                    {"order": self.name},
                    ["name", "status", "fulfillment_type"],
                    as_dict=True,
                ) if not self.is_dine_in else None,
            )
        )

    def items_list(self, from_item=None):
        table = self._table if self.is_dine_in else None
        items = []
        for item in self.entry_items:
            if item.qty > 0 and (from_item is None or from_item == item.identifier):
                _item = item.as_dict()

                row = {col: _item[col] for col in [
                    "identifier",
                    "item_group",
                    "item_code",
                    "item_name",
                    "qty",
                    "rate",
                    "amount",
                    "discount_percentage",
                    "discount_amount",
                    "price_list_rate",
                    "item_tax_template",
                    "item_tax_rate",
                    "tax_amount",
                    "table_description",
                    "status",
                    "notes",
                    "ordered_time",
                    "ordered_nro",
                    "processing_started_at",
                    "processing_started_by",
                    "completed_at",
                    "completed_by",
                    "waiting_time_minutes",
                    "preparation_time_minutes",
                    "total_time_minutes",
                    "preparation_time_target",
                    "preparation_time_source",
                    "has_batch_no",
                    "batch_no",
                    "has_serial_no",
                    "serial_no",
                    "unit_value",
                    "ordered_finish",
                ]}

                row["order_name"] = item.parent
                row["entry_name"] = item.name
                row["short_name"] = table.order_short_name(item.parent) if table else self.short_name
                row["process_status_data"] = (
                    table.process_status_data(item)
                    if table
                    else self.item_process_status_data(item)
                )

                items.append(row)
        return items

    @property
    def send(self):
        table = self._table if self.is_dine_in else None
        items_to_return = []
        data_to_send = []
        ordered_items = [
            item for item in self.entry_items
            if item.status != status_attending and item.ordered_time
        ]
        ordered_nro = max(
            (frappe.utils.cint(item.ordered_nro) for item in ordered_items),
            default=0,
        ) + 1
        ordered_time = frappe.utils.now_datetime()
        targets = preparation_targets(
            item.item_code
            for item in self.entry_items
            if item.status == status_attending
        )
        for i in self.entry_items:
            item = frappe.get_doc("Order Entry Item", {"identifier": i.identifier})
            if item.status == status_attending:
                items_to_return.append(i.identifier)
                target = targets.get(item.item_code, {"minutes": 0, "source": None})

                item.status = "Sent"
                item.ordered_time = ordered_time
                item.ordered_nro = ordered_nro
                item.preparation_time_target = target["minutes"]
                item.preparation_time_source = target["source"]
                item.processing_started_at = None
                item.processing_started_by = None
                item.completed_at = None
                item.completed_by = None
                item.waiting_time_minutes = 0
                item.preparation_time_minutes = 0
                item.total_time_minutes = 0
                item.ordered_finish = 0
                item.save()

                if table:
                    data_to_send.append(table.get_command_data(item))

        self.reload()
        self.synchronize(dict(status=["Sent"]))
        if not self.is_dine_in:
            from restaurant_management.restaurant_management.doctype.restaurant_fulfillment.restaurant_fulfillment import sync_order_preparation

            sync_order_preparation(self.name)

        return self.data()

    def set_item_note(self, item, notes):
        frappe.db.set_value("Order Entry Item", {"identifier": item}, "notes", notes)
        self.reload()
        item = self.items_list(item)
        self.synchronize(dict(items=item))

    def update_item_details(
        self,
        identifier,
        notes="",
        discount_percentage=0,
        client=None,
    ):
        from restaurant_management.restaurant_management.restaurant_manage import check_exceptions

        check_exceptions(
            dict(name="Table Order", short_name="order", action="write", data=self),
            "You cannot modify an order from another User",
        )

        matching_items = [
            item for item in self.entry_items if item.identifier == identifier
        ]
        if len(matching_items) != 1:
            frappe.throw(_("The selected dish no longer exists"))

        item = matching_items[0]
        if item.status not in (status_attending, "Sent", "Processing"):
            frappe.throw(_("The selected dish can no longer be edited"))

        discount_percentage = flt(discount_percentage)
        if discount_percentage < 0 or discount_percentage > 100:
            frappe.throw(_("Line discount percent must be between 0 and 100"))

        discount_changed = discount_percentage != flt(item.discount_percentage)
        if discount_changed:
            if item.status != status_attending:
                frappe.throw(_("Only unsent dishes can change their discount"))
            if not cint(
                frappe.db.get_value(
                    "POS Profile", self.pos_profile, "allow_discount_change"
                )
            ):
                frappe.throw(_("The POS Profile does not allow changing discounts"))

        entry = item.as_dict()
        entry["notes"] = str(notes or "")
        entry["discount_percentage"] = discount_percentage
        entry["rate"] = flt(item.price_list_rate) * (1 - discount_percentage / 100)

        action = self.update_item(entry)
        if action == "db_commit":
            self.reload()
        self.aggregate()

        return self.synchronize(dict(item=identifier, client=client))

    def update_item_quantity(self, identifier, qty, client=None):
        from restaurant_management.restaurant_management.restaurant_manage import check_exceptions

        check_exceptions(
            dict(name="Table Order", short_name="order", action="write", data=self),
            "You cannot modify an order from another User",
        )

        quantity = flt(qty)
        if quantity < 1 or quantity != cint(quantity):
            frappe.throw(_("Quantity must be a whole number greater than zero"))
        quantity = cint(quantity)

        frappe.db.sql(
            "SELECT name FROM `tabTable Order` WHERE name = %s FOR UPDATE",
            (self.name,),
        )
        self.reload()
        matching_items = [
            item for item in self.entry_items if item.identifier == identifier
        ]
        if len(matching_items) != 1:
            frappe.throw(_("The selected dish no longer exists"))

        item = matching_items[0]
        if item.status != status_attending:
            frappe.throw(_("Only unsent dishes can change their quantity"))

        entry = item.as_dict()
        entry["qty"] = quantity
        entry["status"] = status_attending

        action = self.update_item(entry)
        if action == "db_commit":
            self.reload()
        self.aggregate()

        return self.synchronize(dict(item=identifier, client=client))

    @property
    def get_items(self):
        return self.data()

    @property
    def _delete(self):
        self.normalize_data()
        if len(self.entry_items) > self.products_not_ordered_count:
            frappe.throw(_("There are ordered products, you cannot delete"))

        self.delete()

    def normalize_data(self):
        self.entry_items = []
        for item in self.entry_items:
            if item.qty > 0:
                self.append('entry_items', dict(
                    name=item.name,
                    item_code=item.item_code,
                    qty=item.qty,
                    rate=item.rate,
                    price_list_rate=item.price_list_rate,
                    item_tax_template=item["item_tax_template"],
                    discount_percentage=item.discount_percentage,
                    discount_amount=item.discount_amount,
                    status=item.status,
                    identifier=item.identifier,
                    notes=item.notes,
                    ordered_time=item.ordered_time,
                    ordered_nro=item.ordered_nro,
                    processing_started_at=item.processing_started_at,
                    processing_started_by=item.processing_started_by,
                    completed_at=item.completed_at,
                    completed_by=item.completed_by,
                    waiting_time_minutes=item.waiting_time_minutes,
                    preparation_time_minutes=item.preparation_time_minutes,
                    total_time_minutes=item.total_time_minutes,
                    preparation_time_target=item.preparation_time_target,
                    preparation_time_source=item.preparation_time_source,
                    has_batch_no=item.has_batch_no,
                    batch_no=item.batch_no,
                    has_serial_no=item.has_serial_no,
                    serial_no=item.serial_no,
                    unit_value=item.unit_value,
                    ordered_finish=item.ordered_finish,
                ))
        self.save()

    def after_delete(self):
        if self.is_dine_in:
            self.synchronize(dict(action="Delete", status=["Deleted"]))
        else:
            frappe.publish_realtime(
                "restaurant_fulfillment_update",
                {"order": self.name, "action": "Delete"},
                after_commit=True,
            )
