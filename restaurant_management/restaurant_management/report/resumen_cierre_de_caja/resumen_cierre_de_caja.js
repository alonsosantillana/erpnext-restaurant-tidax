// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Resumen Cierre de Caja"] = {
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
		}
	]
};
