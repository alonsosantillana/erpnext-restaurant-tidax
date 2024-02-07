frappe.ui.form.on("Material Request", {
    refresh: function(frm, cdt, cdn){
		if(frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Resto"), function() {
				frm.events.get_items_from_pos_invoice(frm, cdt, cdn);
                //alert("LOGICA RESTO");
			}, __("Get Items From"));
			//frm.page.set_inner_btn_group_as_primary(__("Make"));
		}
	},

    get_items_from_pos_invoice: function(frm) {
		erpnext.utils.map_current_doc({
			method: "restaurant_management.restaurant_management.doctype.utils.make_material_request", //ANALIZAR
			source_doctype: "POS Invoice",
			target: frm,
			setters: {
				customer: frm.doc.customer || undefined,
				posting_date: undefined,
			},
			get_query_filters: {
				docstatus: 1,
				//status: ["not in", ["Closed", "On Hold"]],
				//per_delivered: ["<", 99.99],
				company: frm.doc.company
			}
		});
	},
});
