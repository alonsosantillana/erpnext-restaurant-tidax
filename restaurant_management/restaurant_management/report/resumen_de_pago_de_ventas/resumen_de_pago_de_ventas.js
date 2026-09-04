// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Resumen de pago de ventas"] = {
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
			"fieldname": "report_date_from",
			"label": __("From Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "report_date_to",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "pos_profile",
			"label": __("Perfil POS"),
			"fieldtype": "Link",
			"options": "POS Profile",
			"get_query": () => ({
				"filters": {
					"company": frappe.query_report.get_filter_value("company")
				}
			})
		},
		{
			"fieldname": "user_cajero",
			"label": __("Usuario que cobró"),
			"fieldtype": "Link",
			"options": "User",
			"get_query": () => ({
				"filters": {
					"enabled": 1
				}
			})
		},
		{
			"fieldname": "pos_opening_entry",
			"label": __("Apertura POS"),
			"fieldtype": "Link",
			"options": "POS Opening Entry",
			"get_query": () => {
				const filters = {
					"company": frappe.query_report.get_filter_value("company"),
					"docstatus": 1
				};
				const pos_profile = frappe.query_report.get_filter_value("pos_profile");
				const user = frappe.query_report.get_filter_value("user_cajero");
				if (pos_profile) {
					filters.pos_profile = pos_profile;
				}
				if (user) {
					filters.user = user;
				}
				return { filters };
			}
		}
	]
};
