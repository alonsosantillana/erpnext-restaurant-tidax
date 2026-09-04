# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(filters), get_data(filters)


def get_data(filters):
	filters = frappe._dict(filters or {})
	filters.invoice_status = "Consolidated"
	filters.empty_value = ""
	conditions = [
		"invoice.company = %(company)s",
		"invoice.posting_date BETWEEN %(report_date_from)s AND %(report_date_to)s",
		"invoice.docstatus = 1",
		"table_order.docstatus = 1",
		"invoice_item.docstatus = 1",
		"invoice.status = %(invoice_status)s",
		"invoice.is_return = 0",
		"invoice_item.qty > 0",
	]
	if filters.get("user_mozo"):
		conditions.append(
			"COALESCE(NULLIF(table_order.cambio_mozo, %(empty_value)s), table_order.owner) = %(user_mozo)s"
		)

	return frappe.db.sql(
		f"""
			SELECT
				invoice.posting_date AS fecha,
				COALESCE(NULLIF(table_order.cambio_mozo, %(empty_value)s), table_order.owner) AS mozo,
				user.full_name AS nombre,
				invoice_item.item_group AS grupo_platos,
				invoice_item.item_code AS codigo_platos,
				invoice_item.item_name AS nombre_platos,
				SUM(invoice_item.qty) AS qty_platos_atendidos
			FROM `tabTable Order` AS table_order
			INNER JOIN `tabPOS Invoice` AS invoice
				ON invoice.name = table_order.link_invoice
			INNER JOIN `tabPOS Invoice Item` AS invoice_item
				ON invoice_item.parent = invoice.name
			LEFT JOIN `tabUser` AS user
				ON user.name = COALESCE(
					NULLIF(table_order.cambio_mozo, %(empty_value)s), table_order.owner
				)
			WHERE {" AND ".join(conditions)}
			GROUP BY
				invoice.posting_date,
				COALESCE(NULLIF(table_order.cambio_mozo, %(empty_value)s), table_order.owner),
				user.full_name,
				invoice_item.item_group,
				invoice_item.item_code,
				invoice_item.item_name
			ORDER BY
				invoice.posting_date,
				user.full_name,
				invoice_item.item_group,
				invoice_item.item_name
		""",
		filters,
		as_dict=True,
	)


def get_columns(filters=None):
	return [
		"Fecha:Date:100",
		"Mozo:Data:200",
		"Nombre:Data:200",
		"Grupo Platos:Data:200",
		"Codigo Platos:Data:100",
		"Nombre Platos:Data:200",
		"QTY Platos Atendidos:Float:100",
	]
