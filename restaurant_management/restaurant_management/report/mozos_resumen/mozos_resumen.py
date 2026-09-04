# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_validate_filters(filters)
	data = get_data(filters)
	if data:
		data.append(_get_total_row(data))
	return get_columns(), data, None, None, None, True


def _validate_filters(filters):
	for fieldname, label in (
		("company", _("Company")),
		("report_date_from", _("From Date")),
		("report_date_to", _("To Date")),
	):
		if not filters.get(fieldname):
			frappe.throw(_("{0} is required").format(label))

	if getdate(filters.report_date_from) > getdate(filters.report_date_to):
		frappe.throw(_("From Date cannot be after To Date"))


def get_data(filters):
	filters = frappe._dict(filters or {})
	filters.invoice_status = "Consolidated"
	filters.empty_value = ""
	filters.user_mozo = filters.get("user_mozo") or ""

	return frappe.db.sql(
		"""
			WITH waiter_summary AS (
				SELECT
					invoice.posting_date AS fecha,
					COALESCE(
						NULLIF(table_order.cambio_mozo, %(empty_value)s),
						table_order.owner
					) AS mozo,
					user.full_name AS nombre,
					COUNT(DISTINCT invoice.name) AS qty_mesas_atendidas,
					ROUND(SUM(invoice.grand_total), 2) AS monto_neto_mesas_atendidas,
					ROUND(SUM(invoice.total), 2) AS monto_bruto_mesas_atendidas,
					SUM(invoice.total_qty) AS qty_platos_atendidos,
					SUM(table_order.guest_count) AS qty_personas_atendidas
				FROM `tabTable Order` AS table_order
				INNER JOIN `tabPOS Invoice` AS invoice
					ON invoice.name = table_order.link_invoice
				LEFT JOIN `tabUser` AS user
					ON user.name = COALESCE(
						NULLIF(table_order.cambio_mozo, %(empty_value)s),
						table_order.owner
					)
				WHERE
					invoice.company = %(company)s
					AND invoice.posting_date BETWEEN %(report_date_from)s AND %(report_date_to)s
					AND invoice.docstatus = 1
					AND table_order.docstatus = 1
					AND invoice.status = %(invoice_status)s
					AND invoice.is_return = 0
				GROUP BY
					invoice.posting_date,
					COALESCE(
						NULLIF(table_order.cambio_mozo, %(empty_value)s),
						table_order.owner
					),
					user.full_name
			),
			daily_totals AS (
				SELECT
					fecha,
					SUM(monto_neto_mesas_atendidas) AS total_neto_dia,
					SUM(monto_bruto_mesas_atendidas) AS total_bruto_dia
				FROM waiter_summary
				GROUP BY fecha
			)
			SELECT
				summary.fecha,
				summary.mozo,
				summary.nombre,
				summary.qty_mesas_atendidas,
				summary.monto_neto_mesas_atendidas,
				summary.monto_bruto_mesas_atendidas,
				summary.qty_platos_atendidos,
				summary.qty_personas_atendidas,
				ROUND(
					summary.monto_neto_mesas_atendidas
					/ NULLIF(daily.total_neto_dia, 0) * 100,
					2
				) AS porcentaje_ventas_neto,
				ROUND(
					summary.monto_bruto_mesas_atendidas
					/ NULLIF(daily.total_bruto_dia, 0) * 100,
					2
				) AS porcentaje_ventas_bruto,
				ROUND(
					summary.monto_neto_mesas_atendidas
					/ NULLIF(summary.qty_mesas_atendidas, 0),
					2
				) AS ticket_promedio_neto,
				ROUND(
					summary.monto_bruto_mesas_atendidas
					/ NULLIF(summary.qty_mesas_atendidas, 0),
					2
				) AS ticket_promedio_bruto,
				daily.total_neto_dia,
				daily.total_bruto_dia
			FROM waiter_summary AS summary
			INNER JOIN daily_totals AS daily ON daily.fecha = summary.fecha
			WHERE
				%(user_mozo)s = %(empty_value)s
				OR summary.mozo = %(user_mozo)s
			ORDER BY
				summary.fecha,
				summary.monto_neto_mesas_atendidas DESC,
				summary.nombre
		""",
		filters,
		as_dict=True,
	)


def _get_total_row(data):
	daily_totals = {
		row.fecha: (flt(row.total_neto_dia), flt(row.total_bruto_dia))
		for row in data
	}
	total_mesas = sum(row.qty_mesas_atendidas or 0 for row in data)
	total_neto = sum(flt(row.monto_neto_mesas_atendidas) for row in data)
	total_bruto = sum(flt(row.monto_bruto_mesas_atendidas) for row in data)
	company_neto = sum(value[0] for value in daily_totals.values())
	company_bruto = sum(value[1] for value in daily_totals.values())

	return frappe._dict(
		mozo=_("Total"),
		qty_mesas_atendidas=total_mesas,
		monto_neto_mesas_atendidas=total_neto,
		monto_bruto_mesas_atendidas=total_bruto,
		qty_platos_atendidos=sum(flt(row.qty_platos_atendidos) for row in data),
		qty_personas_atendidas=sum(row.qty_personas_atendidas or 0 for row in data),
		porcentaje_ventas_neto=flt(total_neto / company_neto * 100, 2) if company_neto else 0,
		porcentaje_ventas_bruto=flt(total_bruto / company_bruto * 100, 2) if company_bruto else 0,
		ticket_promedio_neto=flt(total_neto / total_mesas, 2) if total_mesas else 0,
		ticket_promedio_bruto=flt(total_bruto / total_mesas, 2) if total_mesas else 0,
	)


def get_columns(filters=None):
	return [
		{"fieldname": "fecha", "label": _("Fecha"), "fieldtype": "Date", "width": 100},
		{"fieldname": "mozo", "label": _("Mozo"), "fieldtype": "Data", "width": 200},
		{"fieldname": "nombre", "label": _("Nombre"), "fieldtype": "Data", "width": 100},
		{
			"fieldname": "qty_mesas_atendidas",
			"label": _("QTY Mesas Atendidas"),
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"fieldname": "monto_neto_mesas_atendidas",
			"label": _("Venta Final Cobrada"),
			"fieldtype": "Currency",
			"width": 150,
		},
		{
			"fieldname": "monto_bruto_mesas_atendidas",
			"label": _("Venta Antes de Descuento"),
			"fieldtype": "Currency",
			"width": 170,
		},
		{
			"fieldname": "qty_platos_atendidos",
			"label": _("QTY Platos Atendidos"),
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"fieldname": "qty_personas_atendidas",
			"label": _("QTY Personas Atendidas"),
			"fieldtype": "Int",
			"width": 100,
		},
		{
			"fieldname": "porcentaje_ventas_neto",
			"label": _("Porcentaje Ventas Neto"),
			"fieldtype": "Percent",
			"width": 120,
		},
		{
			"fieldname": "porcentaje_ventas_bruto",
			"label": _("Porcentaje Ventas Bruto"),
			"fieldtype": "Percent",
			"width": 120,
		},
		{
			"fieldname": "ticket_promedio_neto",
			"label": _("Ticket Promedio Neto"),
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"fieldname": "ticket_promedio_bruto",
			"label": _("Ticket Promedio Bruto"),
			"fieldtype": "Currency",
			"width": 140,
		},
	]
