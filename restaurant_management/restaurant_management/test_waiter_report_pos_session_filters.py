import unittest
from unittest.mock import patch

import frappe

from restaurant_management.restaurant_management.report.mozos_resumen import (
	mozos_resumen,
)
from restaurant_management.restaurant_management.report.mozos_vs_platos import (
	mozos_vs_platos,
)


BASE_FILTERS = {
	"company": "ERPCLOUD SAC",
	"report_date_from": "2026-09-05",
	"report_date_to": "2026-09-05",
}


class TestWaiterReportPOSSessionFilters(unittest.TestCase):
	def _assert_session_filters(self, report_module):
		filters = frappe._dict(
			{
				**BASE_FILTERS,
				"pos_opening_entry": "POS-OPE-ECS-2026-00001",
				"pos_closing_entry": "POS-CLO-ECS-2026-00001",
			}
		)
		with patch.object(frappe.db, "sql", return_value=[]) as sql:
			report_module.get_data(filters)

		query, values = sql.call_args.args[:2]
		self.assertIn("invoice.restaurant_pos_opening_entry", query)
		self.assertIn("session_closing.pos_opening_entry", query)
		self.assertIn("selected_closing.name = %(pos_closing_entry)s", query)
		self.assertEqual(values.pos_opening_entry, "POS-OPE-ECS-2026-00001")
		self.assertEqual(values.pos_closing_entry, "POS-CLO-ECS-2026-00001")

	def test_mozos_vs_platos_filters_by_pos_session(self):
		self._assert_session_filters(mozos_vs_platos)

	def test_mozos_resumen_filters_by_pos_session(self):
		self._assert_session_filters(mozos_resumen)


if __name__ == "__main__":
	unittest.main()
