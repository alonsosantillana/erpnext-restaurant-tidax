import frappe


def execute():
	for settings in frappe.get_all("Restaurant Company Settings", fields=["name", "company"]):
		updates = {}
		if not frappe.db.get_value(
			"Restaurant Company Settings", settings.name, "default_expense_account"
		):
			account = frappe.db.get_value(
				"Account",
				{
					"company": settings.company,
					"account_name": "Gastos Varios",
					"root_type": "Expense",
					"is_group": 0,
					"disabled": 0,
				},
				"name",
			)
			if account:
				updates["default_expense_account"] = account

		if not frappe.db.get_value(
			"Restaurant Company Settings", settings.name, "expense_cost_center"
		):
			cost_center = frappe.db.get_value("Company", settings.company, "cost_center")
			if cost_center:
				updates["expense_cost_center"] = cost_center

		if updates:
			frappe.db.set_value(
				"Restaurant Company Settings", settings.name, updates, update_modified=False
			)
