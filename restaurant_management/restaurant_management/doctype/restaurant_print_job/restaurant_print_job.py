import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class RestaurantPrintJob(Document):
	def autoname(self):
		abbreviation = frappe.get_cached_value("Company", self.company, "abbr")
		self.name = make_autoname(f"RPJ-{abbreviation}-.YYYY.-.#####")

	def validate(self):
		if self.status not in {
			"Pending", "Sending", "Accepted by HWB", "Failed", "Ambiguous", "Cancelled"
		}:
			frappe.throw(_("Invalid restaurant print job status"))
		station_company = frappe.db.get_value("Restaurant Print Station", self.station, "company")
		if station_company != self.company:
			frappe.throw(_("Print job and station must belong to the same company"))
