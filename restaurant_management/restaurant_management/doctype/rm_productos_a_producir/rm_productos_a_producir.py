# Copyright (c) 2023, Quantum Bit Core and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class RMPRODUCTOSAPRODUCIR(Document):
	def validate(self):
		self.rm_pp_cantprod = len(self.rm_pp_producto or [])
