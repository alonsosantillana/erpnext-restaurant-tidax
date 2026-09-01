import base64
import unittest

from restaurant_management.thermal_print import (
	build_pos_invoice_escpos,
	build_table_order_account_escpos,
	qr_svg_data_uri,
)


class TestThermalPrintHelpers(unittest.TestCase):
	def test_qr_svg_data_uri_is_self_contained(self):
		value = qr_svg_data_uri("20123456789|03|B001|1|18.00|118.00")

		self.assertTrue(value.startswith("data:image/svg+xml;base64,"))
		svg = base64.b64decode(value.split(",", 1)[1])
		self.assertIn(b"<svg", svg)
		self.assertIn(b"#000000", svg)

	def test_empty_qr_value_is_not_rendered(self):
		self.assertEqual(qr_svg_data_uri(None), "")


	def test_escpos_receipt_contains_fiscal_content_qr_and_cut(self):
		doc = {
			"name": "BV-BRE1-000012",
			"company": "ADDERA PERU SAC",
			"currency": "PEN",
			"posting_date": "2026-08-31",
			"posting_time": "12:30:00",
			"customer_name": "Cliente Prueba",
			"tax_id": "12345678",
			"tipo_comprobante": "Boleta de Venta",
			"items": [{
				"item_code": "PLT-001",
				"item_name": "CEVICHE",
				"qty": 2,
				"rate": 35,
				"amount": 70,
				"discount_percentage": 0,
			}],
			"net_total": 59.32,
			"total_taxes_and_charges": 10.68,
			"discount_amount": 0,
			"grand_total": 70,
			"payments": [{"mode_of_payment": "Efectivo", "amount": 70}],
			"codigo_qr_sunat": "20547172966|03|BRE1|12|10.68|70.00",
			"codigo_hash_sunat": "hash-prueba",
			"estado_sunat": "Aceptado",
		}

		raw = build_pos_invoice_escpos(
			doc,
			company_tax_id="20547172966",
			tip={"amount": 5, "mode_of_payment": "Efectivo"},
		)

		self.assertTrue(raw.startswith(b"\x1b@\x1bt\x02"))
		self.assertIn(b"BV-BRE1-000012", raw)
		self.assertIn(b"CANT DESCRIPCION", raw)
		self.assertIn(b"PU", raw)
		self.assertIn(b"CEVICHE", raw)
		self.assertNotIn(b"PLT-001", raw)
		self.assertIn(b"TOTAL", raw)
		self.assertIn(b"PROPINA", raw)
		self.assertIn(b"\x1d(k", raw)
		self.assertTrue(raw.endswith(b"\x1dVB\x00"))

	def test_product_columns_use_the_full_48_character_width(self):
		doc = {
			"company": "ERPCLOUD SAC",
			"currency": "PEN",
			"items": [{
				"item_code": "PLT-001",
				"item_name": "CEVICHE",
				"qty": 2,
				"rate": 35,
				"amount": 70,
			}],
			"grand_total": 70,
		}

		raw = build_pos_invoice_escpos(doc)
		text = raw.decode("cp850", errors="ignore")
		lines = text.splitlines()
		header = next(line for line in lines if "DESCRIPCION" in line).rsplit("\x00", 1)[-1]
		item = next(line for line in lines if "CEVICHE" in line).rsplit("\x00", 1)[-1]

		self.assertEqual(len(header), 48)
		self.assertEqual(len(item), 48)
		self.assertNotIn("PLT-001", text)

	def test_discount_does_not_become_change(self):
		doc = {
			"company": "ERPCLOUD SAC",
			"currency": "PEN",
			"items": [],
			"net_total": 67.45,
			"total_taxes_and_charges": 15.85,
			"discount_amount": 14.70,
			"grand_total": 83.30,
			"change_amount": 14.70,
			"payments": [
				{"mode_of_payment": "Efectivo", "amount": 3.30},
				{"mode_of_payment": "BCP SOL", "amount": 80},
			],
		}

		raw = build_pos_invoice_escpos(doc)

		self.assertIn(b"Descuento", raw)
		self.assertNotIn(b"Vuelto", raw)

	def test_real_payment_excess_is_printed_as_change(self):
		doc = {
			"company": "ERPCLOUD SAC",
			"currency": "PEN",
			"items": [],
			"grand_total": 83.30,
			"payments": [{"mode_of_payment": "Efectivo", "amount": 100}],
		}

		raw = build_pos_invoice_escpos(doc)

		self.assertIn(b"Vuelto", raw)
		self.assertIn(b"S/. 16.70", raw)

	def test_escpos_repeats_complete_ticket_for_each_copy(self):
		doc = {
			"name": "BV-BRE1-000013",
			"company": "ERPCLOUD SAC",
			"currency": "PEN",
			"customer_name": "Cliente",
			"items": [],
			"grand_total": 0,
		}

		raw = build_pos_invoice_escpos(doc, copies=2)

		self.assertEqual(raw.count(b"\x1b@"), 2)
		self.assertEqual(raw.count(b"\x1dVB\x00"), 2)

	def test_escpos_pre_account_is_non_fiscal_and_consolidates_items(self):
		doc = {
			"name": "OR-ADA-2026-00014",
			"company": "ADDERA PERU SAC",
			"creation": "2026-08-31 14:30:00",
			"room_description": "Salon 1",
			"table_description": "T4",
			"guest_count": 2,
			"customer_name": "Cliente Prueba",
			"entry_items": [
				{"item_code": "PLT-001", "item_name": "CEVICHE", "qty": 1, "rate": 35, "amount": 35},
				{"item_code": "PLT-001", "item_name": "CEVICHE", "qty": 2, "rate": 35, "amount": 70},
			],
			"tax": 16.02,
			"amount": 105,
			"discount_global_percent": 10,
		}

		raw = build_table_order_account_escpos(
			doc, company_tax_id="20547172966", waiter_name="Mozo Uno"
		)
		text = raw.decode("cp850", errors="ignore")
		lines = text.splitlines()
		header = next(line for line in lines if "DESCRIPCION" in line).rsplit("\x00", 1)[-1]
		item = next(line for line in lines if "CEVICHE" in line).rsplit("\x00", 1)[-1]

		self.assertIn(b"PRE CUENTA", raw)
		self.assertIn(b"DOCUMENTO NO FISCAL", raw)
		self.assertIn(b"Comensales: 2", raw)
		self.assertIn(b"Mozo: Mozo Uno", raw)
		self.assertEqual(raw.count(b"CEVICHE"), 1)
		self.assertIn(b"PU", raw)
		self.assertNotIn(b"PLT-001", raw)
		self.assertEqual(len(header), 48)
		self.assertEqual(len(item), 48)
		self.assertIn(b"Descuento global", raw)
		self.assertNotIn(b"1Q0", raw)
		self.assertTrue(raw.endswith(b"\x1dVB\x00"))
