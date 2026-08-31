import frappe


def execute():
	"""Move existing pre-account routes to native ESC/POS transport."""
	for route in frappe.get_all(
		"Restaurant Print Route",
		filters={"document_type": "ACCOUNT"},
		fields=["name", "transport_mode"],
	):
		if route.transport_mode != "ESC/POS":
			frappe.db.set_value(
				"Restaurant Print Route",
				route.name,
				"transport_mode",
				"ESC/POS",
				update_modified=False,
			)
