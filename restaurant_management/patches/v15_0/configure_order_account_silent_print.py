import frappe


PRINT_FORMAT = "Order Account"


def execute():
	if "silent_print" not in frappe.get_installed_apps():
		return
	if not frappe.db.exists("Print Format", PRINT_FORMAT):
		return

	settings = frappe.get_single("Restaurant Settings")
	if not settings.print_format:
		settings.print_format = PRINT_FORMAT
		settings.save(ignore_permissions=True)

	if settings.print_format != PRINT_FORMAT:
		return

	if frappe.db.exists("Silent Print Format", PRINT_FORMAT):
		silent_format = frappe.get_doc("Silent Print Format", PRINT_FORMAT)
	else:
		silent_format = frappe.new_doc("Silent Print Format")
		silent_format.print_format = PRINT_FORMAT

	silent_format.page_size = "Custom"
	silent_format.default_print_type = "ORDER"
	silent_format.custom_width = "80mm"
	silent_format.custom_height = "200mm"
	silent_format.custom_margin_left = "3mm"
	silent_format.custom_margin_right = "3mm"
	silent_format.save(ignore_permissions=True)
