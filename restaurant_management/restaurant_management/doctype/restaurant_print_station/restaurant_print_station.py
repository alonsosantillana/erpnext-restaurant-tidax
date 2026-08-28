import frappe
from frappe import _
from frappe.model.document import Document


class RestaurantPrintStation(Document):
	def validate(self):
		if not frappe.db.get_value("User", self.station_user, "enabled"):
			frappe.throw(_("The print station user must be enabled"))
		if self.lease_seconds and self.lease_seconds < 15:
			frappe.throw(_("The station lease must be at least 15 seconds"))
