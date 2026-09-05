// Copyright (c) 2026, Quantum Bit Core and contributors
// For license information, please see license.txt

frappe.ui.form.on("Restaurant Tip", {
	refresh(frm) {
		if (frm.is_new() || ["Cancelled", "Settled"].includes(frm.doc.status) || !can_manage_restaurant_tip()) {
			return;
		}

		frm.add_custom_button(__("Anular propina"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Anular propina"),
				fields: [{
					fieldname: "reason",
					label: __("Motivo de anulación"),
					fieldtype: "Small Text",
					reqd: 1
				}],
				primary_action_label: __("Anular propina"),
				primary_action: async (values) => {
					await frappe.call({
						method: "restaurant_management.restaurant_management.doctype.restaurant_tip.restaurant_tip.cancel_restaurant_tip",
						args: { tip_name: frm.doc.name, reason: values.reason },
						freeze: true,
						freeze_message: __("Anulando propina...")
					});
					dialog.hide();
					await frm.reload_doc();
				}
			});
			dialog.show();
		}, __("Acciones"));

		frm.add_custom_button(__("Rectificar importe"), () => {
			const dialog = new frappe.ui.Dialog({
				title: __("Rectificar importe de propina"),
				fields: [
					{
						fieldname: "new_amount",
						label: __("Nuevo importe"),
						fieldtype: "Currency",
						default: frm.doc.amount,
						reqd: 1
					},
					{
						fieldname: "reason",
						label: __("Motivo de rectificación"),
						fieldtype: "Small Text",
						reqd: 1
					},
					{
						fieldname: "confirm_adjustment",
						label: __("Confirmo que la diferencia fue cobrada o devuelta al cliente"),
						fieldtype: "Check",
						reqd: 1
					}
				],
				primary_action_label: __("Rectificar importe"),
				primary_action: async (values) => {
					const response = await frappe.call({
						method: "restaurant_management.restaurant_management.doctype.restaurant_tip.restaurant_tip.rectify_restaurant_tip",
						args: {
							tip_name: frm.doc.name,
							new_amount: values.new_amount,
							reason: values.reason,
							confirm_adjustment: values.confirm_adjustment
						},
						freeze: true,
						freeze_message: __("Rectificando propina...")
					});
					dialog.hide();
					frappe.set_route("Form", "Restaurant Tip", response.message.tip);
				}
			});
			dialog.show();
		}, __("Acciones"));
	}
});

function can_manage_restaurant_tip() {
	return ["System Manager", "resto_admin", "resto_cajero", "Admin Resto", "Cajero"]
		.some((role) => frappe.user_roles.includes(role));
}
