import frappe


LEGACY_SCRIPT = "CustomScript0024"


def execute():
	"""Retire the site-only POS Invoice button superseded by the company print queue."""
	if not frappe.db.exists("Client Script", LEGACY_SCRIPT):
		return

	script = frappe.db.get_value(
		"Client Script",
		LEGACY_SCRIPT,
		["dt", "enabled", "script"],
		as_dict=True,
	)
	if (
		not script
		or script.dt != "POS Invoice"
		or not script.enabled
		or "silent_print.utils.print_format.print_silently" not in (script.script or "")
	):
		return

	frappe.db.set_value("Client Script", LEGACY_SCRIPT, "enabled", 0)
