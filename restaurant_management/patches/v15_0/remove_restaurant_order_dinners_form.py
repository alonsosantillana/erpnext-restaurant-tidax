import frappe


def execute():
	old_form = "restaurant-order-dinners"
	if frappe.db.exists("Desk Form", old_form):
		frappe.delete_doc("Desk Form", old_form, force=True, ignore_permissions=True)
