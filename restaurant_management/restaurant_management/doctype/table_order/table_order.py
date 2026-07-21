# -*- coding: utf-8 -*-
# Copyright (c) 2021, Quantum Bit Core and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt
import json

from restaurant_management.restaurant_management.page.restaurant_manage.restaurant_manage import RestaurantManage
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


class TableOrder(Document):
    def validate(self):
        self.set_default_customer()
        self.validate_global_discount()

    def on_update(self):
        previous = self.get_doc_before_save()
        if previous and (
            self.has_value_changed("discount")
            or self.has_value_changed("discount_global_percent")
        ):
            self.synchronize(dict(action="Update"))
        elif previous and self.has_value_changed("guest_count"):
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
                    table_description=f'{self.room_description} ({self.table_description})',
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

        self._table.synchronize()

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
    ):
        # TIDAX: obteniendo el perfil del usuario para ver si puede realizar el comprobante
        profile = frappe.db.get_value("User", frappe.session.user, "role_profile_name")
        if profile == "Resto_Mozos" or profile == "Resto_Cocinas":
            return frappe.throw(_("No tiene permisos suficientes para generar el comprobante"))

        if self.link_invoice:
            return frappe.throw(_("The order has been invoiced"))

        customer = str(customer or "").strip()
        voucher_type = str(voucher_type or "").strip()
        emission_mode = str(emission_mode or "").strip()
        guest_count = cint(guest_count)
        if not customer:
            frappe.throw(_("Seleccione un cliente"))
        if guest_count <= 0:
            frappe.throw(_("La cantidad de comensales debe ser mayor que cero"))

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

        series = frappe.db.get_single_value(
            "Restaurant Settings", voucher_config["series_field"]
        )
        if not series:
            frappe.throw(
                _("Configure la serie {0} en Restaurant Settings").format(
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

        invoice.table_description = self.table_description
        invoice.validate()
        invoice.save()
        invoice.submit()

        self.status = "Invoiced"
        self.link_invoice = invoice.name

        # TIDAX
        self.total_amount_discount_lines = total_dicount_lines

        self.save()
        self.submit()

        frappe.msgprint(_('Invoice Created'), indicator='green', alert=True)

        self.synchronize(dict(action="Invoiced", status=["Invoiced"]))

        return dict(
            status=True,
            invoice_name=invoice.name
        )

    def transfer(self, table, client):
        last_table = self._table
        new_table = frappe.get_doc("Restaurant Object", table)

        # last_table.validate_user()
        last_table_name = self.table
        new_table.validate_transaction(self.owner)

        self.table = table

        self.save()

        for i in self.entry_items:
            table_description = f'{self.room_description} ({self.table_description})'
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
                rate = 0 if item["rate"] is None else item["rate"]
                price_list_rate = 0 if item["price_list_rate"] is None else item["price_list_rate"]
                unit_value = 0 if item["unit_value"] is None else item["unit_value"]

                margin_rate_or_amount = (rate - price_list_rate)
                invoice.append('items', dict(
                    identifier=item["identifier"],
                    item_code=item["item_code"],
                    qty=item["qty"],
                    rate=item["rate"],
                    discount_percentage=item["discount_percentage"],

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

    def delete_item(self, item, unrestricted=False, synchronize=True):
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
            self.synchronize(dict(action='queue', item_removed=item, status=[status]))

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
                status="Attending" if entry["status"] in ["Pending", "", None] else entry["status"],
                identifier=entry["identifier"],
                notes=entry["notes"],
                table_description=f'{self.room_description} ({self.table_description})',
                ordered_time=entry["ordered_time"] or frappe.utils.now_datetime(),
                # ordered_nro=nro_orden_result[0]["max_parent"] + 1 if (entry["status"] in ["Attending"]) else nro_orden_result[0]["max_parent"],
                ordered_nro=1,
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
                _data = ','.join('='.join((f"`{key}`", f"'{'' if val is None else val}'")) for (key, val) in data.items())
                frappe.db.sql("""UPDATE `tabOrder Entry Item` set {data} WHERE `identifier` = '{identifier}'""".format(
                    identifier=entry["identifier"], data=_data)
                )
                return "db_commit"

    def calculate_order(self, items):
        entry_items = {item["identifier"]: item for item in items}
        invoice = self.get_invoice(entry_items)

        self.entry_items = []
        for item in invoice.items:
            entry_item = entry_items[item.serial_no] if item.serial_no in entry_items else None

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
                status="Attending" if entry_item["status"] in ["Pending", "", None] else entry_item["status"],
                identifier=entry_item["identifier"],
                notes=entry_item["notes"],
                ordered_time=entry_item["ordered_time"],
                table_description=f'{self.room_description} ({self.table_description})',
                has_batch_no=entry_item["has_batch_no"],
                batch_no=entry_item["batch_no"],
                has_serial_no=entry_item["has_serial_no"],
                serial_no=entry_item["serial_no"],
                # TIDAX : Adicion
                unit_value=entry_item["unit_value"],
                ordered_finish=entry_item["ordered_finish"],
                ordered_nro=entry_item["ordered_nro"]
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
                guest_count=self.guest_count
            )
        )

    def items_list(self, from_item=None):
        table = self._table
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
                    "has_batch_no",
                    "batch_no",
                    "has_serial_no",
                    "serial_no",
                    "unit_value",
                    "ordered_finish",
                ]}

                row["order_name"] = item.parent
                row["entry_name"] = item.name
                row["short_name"] = table.order_short_name(item.parent)
                row["process_status_data"] = table.process_status_data(item)

                items.append(row)
        return items

    @property
    def send(self):
        table = self._table
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
        for i in self.entry_items:
            item = frappe.get_doc("Order Entry Item", {"identifier": i.identifier})
            if item.status == status_attending:
                items_to_return.append(i.identifier)

                item.status = "Sent"
                item.ordered_time = ordered_time
                item.ordered_nro = ordered_nro
                item.save()

                data_to_send.append(table.get_command_data(item))

        self.reload()
        self.synchronize(dict(status=["Sent"]))

        return self.data()

    def set_item_note(self, item, notes):
        frappe.db.set_value("Order Entry Item", {"identifier": item}, "notes", notes)
        self.reload()
        item = self.items_list(item)
        self.synchronize(dict(items=item))

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
                    has_batch_no=item.has_batch_no,
                    batch_no=item.batch_no,
                    has_serial_no=item.has_serial_no,
                    serial_no=item.serial_no,
                    unit_value=item.unit_value,
                    ordered_finish=item.ordered_finish,
                ))
        self.save()

    def after_delete(self):
        self.synchronize(dict(action="Delete", status=["Deleted"]))
