import frappe
from frappe.model.document import Document


class PedidosYaOrder(Document):
    def validate(self):
        if self.table_order:
            order_company = frappe.db.get_value("Table Order", self.table_order, "company")
            if order_company and order_company != self.company:
                frappe.throw("PedidosYa order and restaurant order must use the same company")
