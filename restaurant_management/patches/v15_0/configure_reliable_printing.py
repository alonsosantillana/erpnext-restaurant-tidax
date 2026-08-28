import frappe


def execute():
	if not frappe.db.exists("DocType", "Restaurant Print Station"):
		return
	print_user = frappe.db.get_single_value("Silent Print Settings", "print_user") or "Administrator"
	for settings_name in frappe.get_all("Restaurant Company Settings", pluck="name"):
		settings = frappe.get_doc("Restaurant Company Settings", settings_name)
		station_name = "Caja - {0}".format(settings.company)
		if not frappe.db.exists("Restaurant Print Station", station_name):
			frappe.get_doc({
				"doctype": "Restaurant Print Station",
				"station_name": station_name,
				"company": settings.company,
				"station_user": print_user,
				"enabled": 1,
				"lease_seconds": 45,
			}).insert(ignore_permissions=True)

		configured = {(row.document_type, row.production_center or "") for row in settings.get("print_routes", [])}
		for route_type, format_field, print_type, enabled in (
			("ACCOUNT", "print_format", "ACCOUNT", 1),
			("INVOICE", "print_format_ce", "INVOICE", 1),
			("ORDER", "print_format_order", "ORDER", 0),
		):
			print_format = settings.get(format_field)
			if not print_format or (route_type, "") in configured:
				continue
			settings.append("print_routes", {
				"enabled": enabled,
				"document_type": route_type,
				"station": station_name,
				"print_format": print_format,
				"print_type": print_type,
				"copies": 1,
				"automatic": 1 if route_type == "INVOICE" else 0,
			})
		settings.flags.ignore_permissions = True
		settings.save()
