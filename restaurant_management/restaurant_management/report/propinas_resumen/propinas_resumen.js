// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Propinas Resumen"] = {
	"onload": function(report) {
		if (!can_manage_tips()) return;

		report.page.add_inner_button(__("Pagar al mozo"), () => {
			const rows = get_selected_tips_for_settlement(report);
			if (rows) show_settle_tips_dialog(rows, report);
		}, __("Acciones"));

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


function get_selected_tips_for_settlement(report) {
	const rows = report.get_checked_items().filter((row) => row.name);
	if (!rows.length) {
		frappe.msgprint(__("Seleccione al menos una propina pendiente de pago."));
		return null;
	}
	if (rows.some((row) => row.estado !== "Collected")) {
		frappe.msgprint(__("Solo puede pagar propinas con estado Collected."));
		return null;
	}
	const waiters = new Set(rows.map((row) => row.mozo));
	const closings = new Set(rows.map((row) => row.cierre_pos));
	if (waiters.size !== 1 || closings.size !== 1 || !rows[0].cierre_pos) {
		frappe.msgprint(__("Seleccione propinas de un solo mozo y un mismo cierre POS."));
		return null;
	}
	return rows;
}

function show_settle_tips_dialog(rows, report) {
	const total = rows.reduce((sum, row) => sum + flt(row.propinas), 0);
	const dialog = new frappe.ui.Dialog({
		title: __("Pagar propinas al mozo"),
		fields: [
			{
				fieldname: "summary",
				fieldtype: "HTML",
				options: `<div class="alert alert-info">
					<div><strong>${__("Mozo")}:</strong> ${frappe.utils.escape_html(rows[0].nombre || rows[0].mozo)}</div>
					<div><strong>${__("Cierre POS")}:</strong> ${frappe.utils.escape_html(rows[0].cierre_pos)}</div>
					<div><strong>${__("Propinas")}:</strong> ${rows.length}</div>
					<div><strong>${__("Total a pagar")}:</strong> ${format_currency(total)}</div>
				</div>`
			},
			{
				fieldname: "posting_date",
				label: __("Fecha de pago"),
				fieldtype: "Date",
				default: frappe.datetime.get_today(),
				reqd: 1
			},
			{
				fieldname: "mode_of_payment",
				label: __("Medio de pago al mozo"),
				fieldtype: "Link",
				options: "Mode of Payment",
				reqd: 1
			}
		],
		primary_action_label: __("Registrar pago consolidado"),
		primary_action: async (values) => {
			const response = await frappe.call({
				method: "restaurant_management.restaurant_management.doctype.restaurant_tip.restaurant_tip.settle_restaurant_tips",
				args: {
					tip_names: rows.map((row) => row.name),
					mode_of_payment: values.mode_of_payment,
					posting_date: values.posting_date
				},
				freeze: true,
				freeze_message: __("Registrando pago de propinas...")
			});
			dialog.hide();
			frappe.msgprint(__("Se registró el asiento consolidado {0} por {1}.", [
				response.message.journal_entry,
				format_currency(response.message.total)
			]));
			report.refresh();
		}
	});
	dialog.show();
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
