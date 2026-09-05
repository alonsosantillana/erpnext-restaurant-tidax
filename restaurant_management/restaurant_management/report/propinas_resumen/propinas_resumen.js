// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Propinas Resumen"] = {
	"onload": function(report) {
		if (!can_manage_tips()) return;

		report.page.add_inner_button(__("Anular propina"), () => {
			const row = get_selected_tip(report);
			if (row) show_cancel_tip_dialog(row, report);
		}, __("Acciones"));
		report.page.add_inner_button(__("Rectificar importe"), () => {
			const row = get_selected_tip(report);
			if (row) show_rectify_tip_dialog(row, report);
		}, __("Acciones"));
	},
	"get_datatable_options": function(options) {
		return Object.assign(options, { "checkboxColumn": true });
	},
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"reqd": 1,
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "report_date",
			"label": __("Fecha de propina"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "pos_opening_entry",
			"label": __("Apertura POS"),
			"fieldtype": "Link",
			"options": "POS Opening Entry",
			"get_query": () => ({
				"filters": {
					"company": frappe.query_report.get_filter_value("company"),
					"docstatus": 1
				}
			})
		},
		{
			"fieldname": "pos_closing_entry",
			"label": __("Cierre POS"),
			"fieldtype": "Link",
			"options": "POS Closing Entry",
			"get_query": () => ({
				"filters": {
					"company": frappe.query_report.get_filter_value("company"),
					"docstatus": 1
				}
			})
		},
		{
			"fieldname": "include_cancelled",
			"label": __("Incluir anuladas"),
			"fieldtype": "Check",
			"default": 0
		},
		{
			"fieldname": "user_mozo",
			"label": __("Mozo"),
			"fieldtype": "Link",
			"options": "User"
		}
	]
};

function can_manage_tips() {
	return ["System Manager", "resto_admin", "resto_cajero", "Admin Resto", "Cajero"]
		.some((role) => frappe.user_roles.includes(role));
}

function get_selected_tip(report) {
	const rows = report.get_checked_items();
	if (rows.length !== 1 || !rows[0].name) {
		frappe.msgprint(__("Seleccione exactamente una propina."));
		return null;
	}
	return rows[0];
}

function show_cancel_tip_dialog(row, report) {
	const dialog = new frappe.ui.Dialog({
		title: __("Anular propina {0}", [row.name]),
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
				args: { tip_name: row.name, reason: values.reason },
				freeze: true,
				freeze_message: __("Anulando propina...")
			});
			dialog.hide();
			frappe.show_alert({ message: __("Propina anulada"), indicator: "green" });
			report.refresh();
		}
	});
	dialog.show();
}

function show_rectify_tip_dialog(row, report) {
	const dialog = new frappe.ui.Dialog({
		title: __("Rectificar propina {0}", [row.name]),
		fields: [
			{
				fieldname: "new_amount",
				label: __("Nuevo importe"),
				fieldtype: "Currency",
				default: row.propinas,
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
					tip_name: row.name,
					new_amount: values.new_amount,
					reason: values.reason,
					confirm_adjustment: values.confirm_adjustment
				},
				freeze: true,
				freeze_message: __("Rectificando propina...")
			});
			dialog.hide();
			frappe.msgprint(__("Se creó la propina corregida {0}.", [response.message.tip]));
			report.refresh();
		}
	});
	dialog.show();
}
