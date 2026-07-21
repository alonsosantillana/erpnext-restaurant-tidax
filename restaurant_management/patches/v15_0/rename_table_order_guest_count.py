import frappe


def execute():
	has_dinners = frappe.db.has_column("Table Order", "dinners")
	has_guest_count = frappe.db.has_column("Table Order", "guest_count")

	if has_dinners and not has_guest_count:
		frappe.db.rename_column("Table Order", "dinners", "guest_count")
	elif has_dinners and has_guest_count:
		frappe.db.sql(
			"""
			UPDATE `tabTable Order`
			SET `guest_count` = `dinners`
			WHERE COALESCE(`guest_count`, 0) = 0
			"""
		)
		frappe.db.sql_ddl("ALTER TABLE `tabTable Order` DROP COLUMN `dinners`")
