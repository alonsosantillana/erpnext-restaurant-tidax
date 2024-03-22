# Copyright (c) 2024, Quantum Bit Core and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from datetime import datetime, timedelta
from frappe.model.document import Document

class TableOrderCambioMozo(Document):
	pass

@frappe.whitelist()
def select_mozos_mesas_origen(fecha):
    resultado = frappe.db.sql(
			"""
		SELECT `tabTable Order`.`name`, `tabTable Order`.`owner`, `tabUser`.`full_name`, `tabTable Order`.`cambio_mozo`, `tabTable Order`.`cambio_mozo_nombre` FROM `tabTable Order` 
          INNER JOIN `tabUser` ON `tabUser`.`name` = `tabTable Order`.`owner`
            WHERE DATE(`tabTable Order`.`creation`) = %s
		""",
			fecha, as_dict=True
		)
    return resultado

@frappe.whitelist()
def update_mozos_mesas_origen(orden, cambio_mozo):
    # Actualizar el estado de platos
    resultado = frappe.db.sql(
    """
    UPDATE `tabTable Order` SET owner = %s
    WHERE name = %s
    """,
    (cambio_mozo, orden)
	)
    frappe.db.commit()
    
    return {
			"success": True,
			"msg": "Actualizado Mozo Mesas Origen"
		}
