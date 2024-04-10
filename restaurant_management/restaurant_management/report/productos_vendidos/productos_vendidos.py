# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt

# import frappe


from __future__ import unicode_literals
# from datetime import date
import datetime
from erpnext.setup.doctype import company
from frappe import _
import frappe
import os

def execute(filters=None):
	return get_columns(filters), get_data(filters)

def get_data(filters):
	company = filters.get('company')

	# Diccionario para mapear nombres de mes a números
	meses = {
		'enero': 1,
		'febrero': 2,
		'marzo': 3,
		'abril': 4,
		'mayo': 5,
		'junio': 6,
		'julio': 7,
		'agosto': 8,
		'septiembre': 9,
		'octubre': 10,
		'noviembre': 11,
		'diciembre': 12
	}

	# Obtener year y month en formato str
	year = str(filters.get('year'))
	month_str = str(filters.get('month')).lower()  # Convertir a minúsculas para manejar diferentes formatos de entrada

	# Obtener el número de mes correspondiente
	month = meses.get(month_str)

	# Verificar si el mes es válido
	if month is None:
		# Manejar caso de mes inválido
		print("Mes inválido")
	else:
		# Obtener el primer día del mes
		fecha_inicio = datetime.date(int(year), month, 1)

		# Obtener el último día del mes
		ultimo_dia_mes = datetime.date(int(year), month % 12 + 1, 1) - datetime.timedelta(days=1)
		fecha_fin = ultimo_dia_mes

		# Formatear las fechas para que coincidan con el formato YYYY-MM-DD
		fecha_inicio_str = fecha_inicio.strftime('%Y-%m-%d')
		fecha_fin_str = fecha_fin.strftime('%Y-%m-%d')


	data = frappe.db.sql("""
				SELECT
					YEAR(`tabPOS Invoice`.`posting_date`) AS year,
					MONTH(`tabPOS Invoice`.`posting_date`) AS month,
					`tabPOS Invoice Item`.`item_code` AS codigo_producto,
					`tabPOS Invoice Item`.`item_name` AS nombre_producto, 

					ROUND(SUM(`tabPOS Invoice Item`.`qty`), 2) AS qty,

					SUM(`tabPOS Invoice Item`.`net_amount`) AS monto
				FROM
					`tabPOS Invoice`
				LEFT JOIN
					`tabPOS Invoice Item` ON `tabPOS Invoice`.`name` = `tabPOS Invoice Item`.`parent`
				WHERE
					DATE(`tabPOS Invoice`.`posting_date`) BETWEEN %s AND %s
					AND `tabPOS Invoice`.`docstatus` = 1
					
					AND `tabPOS Invoice Item`.`docstatus` = 1 
				GROUP BY
					YEAR(`tabPOS Invoice`.`posting_date`), MONTH(`tabPOS Invoice`.`posting_date`), `tabPOS Invoice Item`.`item_code`
				ORDER BY
					monto desc;
			""", (fecha_inicio_str, fecha_fin_str), as_dict=True)

	return data

def get_columns(filters=None):
    columns = [
		"Year:Data:100",
		"Month:Data:100",
        "Codigo Producto:Data:100",
        "Nombre Producto:Data:200",

        "QTY:Data:100",

        "monto:Data:100"
    ]

    return columns
