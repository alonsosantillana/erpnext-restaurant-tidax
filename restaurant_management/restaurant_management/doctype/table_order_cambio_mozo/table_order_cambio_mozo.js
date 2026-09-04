// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt

const CAMBIO_MOZO_METHOD =
    "restaurant_management.restaurant_management.doctype.table_order_cambio_mozo.table_order_cambio_mozo";

function cambio_mozo_waiter_query(frm) {
    return {
        query: CAMBIO_MOZO_METHOD + ".search_waiters",
        filters: {
            company: frm.doc.company,
            room: frm.doc.room
        }
    };
}

function cambio_mozo_clear_orders(frm) {
    if (!frm.is_new() || !frm.doc.orden_item || !frm.doc.orden_item.length) return;
    frm.clear_table("orden_item");
    frm.refresh_field("orden_item");
    cambio_mozo_render_summary(frm);
}

function cambio_mozo_render_summary(frm) {
    const rows = frm.doc.orden_item || [];
    const selected = rows.filter(row => cint(row.seleccionar));
    const total = selected.reduce((sum, row) => sum + flt(row.amount), 0);
    const target = frm.doc.nuevo_mozo || __("sin seleccionar");

    let html = "<div class='alert alert-info mb-3'>";
    if (frm.doc.docstatus === 1) {
        html += "<strong>" + __("Reasignación completada") + ":</strong> " +
            frappe.utils.escape_html(frm.doc.resultado || "");
    } else if (!rows.length) {
        html += __("Seleccione los filtros, el nuevo mozo y presione Cargar órdenes activas.");
    } else {
        html += "<strong>" + selected.length + "</strong> " + __("orden(es) seleccionadas") +
            " · <strong>" + format_currency(total) + "</strong>" +
            " · " + __("Destino") + ": <strong>" +
            frappe.utils.escape_html(target) + "</strong>";
    }
    html += "</div>";

    const field = frm.get_field("summary");
    if (field && field.$wrapper) field.$wrapper.html(html);
}

async function cambio_mozo_load_orders(frm) {
    if (!frm.doc.company || !frm.doc.orden_fecha) {
        frappe.msgprint(__("Seleccione la compañía y la fecha."));
        return;
    }

    const response = await frappe.call({
        method: CAMBIO_MOZO_METHOD + ".get_available_orders",
        args: {
            fecha: frm.doc.orden_fecha,
            company: frm.doc.company,
            room: frm.doc.room,
            mozo_origen: frm.doc.mozo_origen
        },
        freeze: true,
        freeze_message: __("Cargando órdenes activas...")
    });

    frm.clear_table("orden_item");
    (response.message || []).forEach(order => {
        const row = frm.add_child("orden_item");
        Object.assign(row, order);
        row.mozo_cambio = frm.doc.nuevo_mozo;
    });
    frm.refresh_field("orden_item");
    frm.dirty();
    cambio_mozo_render_summary(frm);

    if (!(response.message || []).length) {
        frappe.show_alert({
            message: __("No se encontraron órdenes activas con los filtros seleccionados."),
            indicator: "orange"
        });
    }
}

frappe.ui.form.on("Table Order Cambio Mozo", {
    setup(frm) {
        frm.set_query("room", () => ({
            filters: {
                type: "Room",
                company: frm.doc.company
            }
        }));
        frm.set_query("nuevo_mozo", () => cambio_mozo_waiter_query(frm));
        frm.set_query("mozo_origen", () => ({
            query: CAMBIO_MOZO_METHOD + ".search_current_waiters",
            filters: {
                company: frm.doc.company,
                fecha: frm.doc.orden_fecha,
                room: frm.doc.room
            }
        }));
    },

    onload(frm) {
        if (frm.is_new() && !frm.doc.company) {
            frm.set_value("company", frappe.defaults.get_user_default("company"));
        }
        if (frm.is_new() && !frm.doc.orden_fecha) {
            frm.set_value("orden_fecha", frappe.datetime.get_today());
        }
    },

    refresh(frm) {
        frm.set_intro(
            __("Solo se cargan órdenes activas de mesas. La reasignación conserva el creador original y queda registrada."),
            "blue"
        );
        cambio_mozo_render_summary(frm);

        if (frm.doc.docstatus === 0 && (frm.doc.orden_item || []).length) {
            frm.add_custom_button(__("Seleccionar todas"), () => {
                (frm.doc.orden_item || []).forEach(row => {
                    frappe.model.set_value(row.doctype, row.name, "seleccionar", 1);
                });
                cambio_mozo_render_summary(frm);
            }, __("Selección"));
            frm.add_custom_button(__("Limpiar selección"), () => {
                (frm.doc.orden_item || []).forEach(row => {
                    frappe.model.set_value(row.doctype, row.name, "seleccionar", 0);
                });
                cambio_mozo_render_summary(frm);
            }, __("Selección"));
        }
    },

    company(frm) {
        frm.set_value("room", null);
        frm.set_value("mozo_origen", null);
        frm.set_value("nuevo_mozo", null);
        cambio_mozo_clear_orders(frm);
    },

    orden_fecha: cambio_mozo_clear_orders,
    room: cambio_mozo_clear_orders,
    mozo_origen: cambio_mozo_clear_orders,

    nuevo_mozo(frm) {
        (frm.doc.orden_item || []).forEach(row => {
            frappe.model.set_value(
                row.doctype,
                row.name,
                "mozo_cambio",
                frm.doc.nuevo_mozo
            );
        });
        cambio_mozo_render_summary(frm);
    },

    cargar_ordenes(frm) {
        return cambio_mozo_load_orders(frm);
    },

    validate(frm) {
        const selected = (frm.doc.orden_item || []).filter(row => cint(row.seleccionar));
        if (!selected.length) {
            frappe.throw(__("Seleccione por lo menos una orden."));
        }
        if (!frm.doc.nuevo_mozo) {
            frappe.throw(__("Seleccione el nuevo mozo."));
        }
    }
});

frappe.ui.form.on("Table Order Cambio Mozo Detalle", {
    seleccionar(frm) {
        cambio_mozo_render_summary(frm);
    }
});
