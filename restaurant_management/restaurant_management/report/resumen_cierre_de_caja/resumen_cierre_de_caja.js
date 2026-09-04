// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
/* eslint-disable */

const get_resumen_cierre_de_caja_filters = (filters) =>
	Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== undefined && value !== null && value !== ""));

frappe.query_reports["Resumen Cierre de Caja"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			reqd: 1,
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "report_date_from",
			label: __("From Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "report_date_to",
			label: __("To Date"),
			fieldtype: "Date",
			reqd: 1,
			default: frappe.datetime.get_today(),
		},
		{
			fieldname: "pos_profile",
			label: __("POS Profile"),
			fieldtype: "Link",
			options: "POS Profile",
			get_query: () => ({
				filters: { company: frappe.query_report.get_filter_value("company") },
			}),
		},
		{
			fieldname: "user_cajero",
			label: __("Usuario del cierre"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "pos_opening_entry",
			label: __("Apertura POS"),
			fieldtype: "Link",
			options: "POS Opening Entry",
			get_query: () => ({
				filters: get_resumen_cierre_de_caja_filters({
					company: frappe.query_report.get_filter_value("company"),
					pos_profile: frappe.query_report.get_filter_value("pos_profile"),
					user: frappe.query_report.get_filter_value("user_cajero"),
					docstatus: 1,
				}),
			}),
		},
		{
			fieldname: "pos_closing_entry",
			label: __("Cierre POS"),
			fieldtype: "Link",
			options: "POS Closing Entry",
			get_query: () => ({
				filters: get_resumen_cierre_de_caja_filters({
					company: frappe.query_report.get_filter_value("company"),
					pos_profile: frappe.query_report.get_filter_value("pos_profile"),
					user: frappe.query_report.get_filter_value("user_cajero"),
					pos_opening_entry: frappe.query_report.get_filter_value("pos_opening_entry"),
					docstatus: 1,
				}),
			}),
		},
	],
	formatter(value, row, column, data, default_formatter) {
		if (data && data.is_total && column.fieldname === "fecha") {
			return `<strong>${__("Total")}</strong>`;
		}

		const formatted_value = default_formatter(value, row, column, data);
		return data && data.is_total ? `<strong>${formatted_value}</strong>` : formatted_value;
	},
};
