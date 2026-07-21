import frappe


def execute():
	if frappe.db.has_column("Table Order", "personas"):
		frappe.db.sql_ddl("ALTER TABLE `tabTable Order` DROP COLUMN `personas`")
