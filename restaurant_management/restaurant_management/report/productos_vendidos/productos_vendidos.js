// Copyright (c) 2024, Quantum Bit Core and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Productos Vendidos"] = {
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
			"fieldname":"year",
			"label": __("Year"),
			"fieldtype": "Select",
			"options": '2024\n2025\n2026\n2027\n2028\n2029\n2030',
			"default": "2024"
		},
		{
			"fieldname":"month",
			"label": __("Month"),
			"fieldtype": "Select",
			"options": 'Enero\nFebrero\nMarzo\nAbril\nMayo\nJunio\nJulio\nAgosto\nSetiembre\nOctubre\nNoviembre\nDiciembre',
			"default": "Enero"
		}
	]
};
