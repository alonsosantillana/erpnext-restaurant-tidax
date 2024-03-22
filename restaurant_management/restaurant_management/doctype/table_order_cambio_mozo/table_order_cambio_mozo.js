// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
cur_frm.add_fetch('orden', 'owner', 'mozo');
cur_frm.add_fetch('mozo_cambio', 'full_name', 'mozo_cambio_nombre');

cur_frm.fields_dict['orden_item'].grid.get_field('orden').get_query = function(doc, cdt, cdn){
	return {
		filters: {
			"creation": doc.orden_fecha
		}
	}
}

frappe.ui.form.on('Table Order Cambio Mozo', {
	//refresh: function(frm) {

	//}
	on_submit: function(frm) {
        if (frm.doc.orden_fecha) {
            frm.doc.orden_item.forEach(function(item) {
                if(item.mozo_cambio) {
                    // Llama a tu función de actualización de mozos y mesas aquí
                    frappe.call({
                        method: "restaurant_management.restaurant_management.doctype.table_order_cambio_mozo.table_order_cambio_mozo.update_mozos_mesas_origen",
                        args: {
                            orden: item.orden,
                            cambio_mozo: item.mozo_cambio
                        },
                        callback: function(data) {
                            if (!data.message.success) {
                                frappe.throw(data.message.errors);
                            } else {
                                frm.doc.resultado = data.message.msg;
                                refresh_field("resultado");
                            }
                        }
                    });
                }
            });
        } else {
            frappe.msgprint("No hay nada que modificar");
        }
    },

	orden_fecha: function(frm, cdt, cdn) {
		if(frm.doc.orden_fecha){
            frappe.call({
                method: "restaurant_management.restaurant_management.doctype.table_order_cambio_mozo.table_order_cambio_mozo.select_mozos_mesas_origen",
                args: {
                    fecha: frm.doc.orden_fecha
                }
            }).done((r)=>{
                frm.doc.orden_item = [];
                $.each(r.message, function(_i, e){
                    let entry_pm = frm.add_child("orden_item");
                    entry_pm.orden = e.name;
                    entry_pm.mozo = e.owner;
					entry_pm.mozo_nombre = e.full_name;
                    entry_pm.mozo_cambio = e.cambio_mozo;
					entry_pm.mozo_cambio_nombre = e.cambio_mozo_nombre;       
                })             
                refresh_field("orden_item");
            });
        }
        else{
            msgprint("Ingrese una fecha");
        }
	},		
});
