import json

import frappe


PRINT_FORMAT = "Order"


def execute():
	if not frappe.db.exists("Print Format", PRINT_FORMAT):
		return

	fixture_path = frappe.get_app_path(
		"restaurant_management",
		"restaurant_management",
		"print_format",
		"order",
		"order.json",
	)
	with open(fixture_path, encoding="utf-8") as fixture_file:
		fixture = json.load(fixture_file)

	print_format = frappe.get_doc("Print Format", PRINT_FORMAT)
	print_format.html = fixture["html"]
	print_format.flags.ignore_permissions = True
	print_format.flags.ignore_version = True
	print_format.save()
