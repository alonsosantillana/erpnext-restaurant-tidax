from pathlib import Path

import frappe


FORMAT_NAME = "Restaurant POS Invoice 80mm"
LEGACY_FORMAT = "Return POS Invoice"


def _template_html():
	path = Path(
		frappe.get_app_path(
			"restaurant_management",
			"templates",
			"print_formats",
			"restaurant_pos_invoice_80mm.html",
		)
	)
	return path.read_text(encoding="utf-8")


def _upsert_print_format():
	name = frappe.db.exists("Print Format", FORMAT_NAME)
	doc = frappe.get_doc("Print Format", name) if name else frappe.new_doc("Print Format")
	doc.update(
		{
			"name": FORMAT_NAME,
			"doc_type": "POS Invoice",
			"module": "Restaurant Management",
			"custom_format": 1,
			"print_format_type": "Jinja",
			"raw_printing": 0,
			"disabled": 0,
			"default_print_language": "es",
			"pdf_generator": "wkhtmltopdf",
			"margin_top": 0,
			"margin_bottom": 0,
			"margin_left": 0,
			"margin_right": 0,
			"html": _template_html(),
		}
	)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_version = True
	doc.save() if name else doc.insert()


def _upsert_silent_print_format():
	if not frappe.db.exists("DocType", "Silent Print Format"):
		return
	name = frappe.db.exists("Silent Print Format", FORMAT_NAME)
	doc = (
		frappe.get_doc("Silent Print Format", name)
		if name
		else frappe.new_doc("Silent Print Format")
	)
	doc.update(
		{
			"name": FORMAT_NAME,
			"print_format": FORMAT_NAME,
			"default_print_type": "INVOICE",
			"page_size": "Custom",
			"custom_width": "80",
			"custom_height": "300",
			"custom_margin_left": "0",
			"custom_margin_right": "0",
		}
	)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_version = True
	doc.save() if name else doc.insert()


def _migrate_company_routes():
	if not frappe.db.exists("DocType", "Restaurant Company Settings"):
		return
	for settings_name in frappe.get_all("Restaurant Company Settings", pluck="name"):
		settings = frappe.get_doc("Restaurant Company Settings", settings_name)
		changed = False
		if not settings.print_format_ce or settings.print_format_ce == LEGACY_FORMAT:
			settings.print_format_ce = FORMAT_NAME
			changed = True
		for route in settings.get("print_routes", []):
			if route.document_type != "INVOICE":
				continue
			if not route.print_format or route.print_format == LEGACY_FORMAT:
				route.print_format = FORMAT_NAME
				changed = True
		if changed:
			settings.flags.ignore_permissions = True
			settings.flags.ignore_version = True
			settings.save()


def execute():
	_upsert_print_format()
	_upsert_silent_print_format()
	_migrate_company_routes()
