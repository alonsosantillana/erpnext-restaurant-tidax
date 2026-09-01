import frappe


WORKSPACE = "Restaurant Management"
LEGACY_SETTINGS = "Restaurant Settings"
COMPANY_SETTINGS = "Restaurant Company Settings"


def execute():
	if not frappe.db.table_exists("Workspace Link"):
		return

	links = frappe.get_all(
		"Workspace Link",
		filters={
			"parent": WORKSPACE,
			"parenttype": "Workspace",
			"link_to": LEGACY_SETTINGS,
		},
		pluck="name",
	)

	for link in links:
		frappe.db.set_value(
			"Workspace Link",
			link,
			{
				"label": "Configuración por empresa",
				"link_to": COMPANY_SETTINGS,
			},
			update_modified=False,
		)

	frappe.clear_cache(doctype="Workspace")
