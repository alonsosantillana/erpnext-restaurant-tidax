// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Mozos vs Platos"] = {
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
			"get_query": () => {
				const filters = {
					"company": frappe.query_report.get_filter_value("company"),
					"docstatus": 1
				};
				const opening = frappe.query_report.get_filter_value("pos_opening_entry");
				if (opening) filters.pos_opening_entry = opening;
				return { filters };
			}
		},
		{
			"fieldname": "user_mozo",
			"label": __("Mozo"),
			"fieldtype": "Link",
			"options": "User"
		}
	]
};
