// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Propinas Resumen"] = {
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
			"label": __("Posting Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "user_mozo",
			"label": __("Mozo"),
			"fieldtype": "Link",
			"options": "User"
		}
	]
};

