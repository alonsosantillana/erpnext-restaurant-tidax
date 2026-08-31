"""Thermal printing helpers for PDF and native ESC/POS output."""

from base64 import b64encode
from html import unescape
from io import BytesIO
import re
import textwrap


ESC = b"\x1b"
GS = b"\x1d"
DEFAULT_COLUMNS = 48


def qr_svg_data_uri(value):
	"""Return a self-contained, high-contrast QR SVG for wkhtmltopdf."""
	if not value:
		return ""

	from pyqrcode import create as create_qr

	stream = BytesIO()
	try:
		create_qr(str(value)).svg(
			stream,
			scale=4,
			quiet_zone=1,
			module_color="#000000",
			background="#ffffff",
		)
		return "data:image/svg+xml;base64,{0}".format(
			b64encode(stream.getvalue()).decode("ascii")
		)
	finally:
		stream.close()


def _value(row, fieldname, default=None):
	if row is None:
		return default
	if hasattr(row, "get"):
		value = row.get(fieldname)
	else:
		value = getattr(row, fieldname, None)
	return default if value is None else value


def _clean_text(value):
	"""Return printable text without HTML or ESC/POS control characters."""
	text = unescape(str(value or ""))
	text = re.sub(r"<br\s*/?>", ", ", text, flags=re.IGNORECASE)
	text = re.sub(r"<[^>]+>", "", text)
	text = text.replace("\x1b", "").replace("\x1d", "")
	return " ".join(text.split())


def _money(value, currency="PEN"):
	prefix = {"PEN": "S/.", "USD": "US$", "EUR": "EUR"}.get(
		str(currency or "").upper(), str(currency or "")
	)
	try:
		amount = float(value or 0)
	except (TypeError, ValueError):
		amount = 0
	return f"{prefix} {amount:,.2f}".strip()


def _number(value):
	try:
		value = float(value or 0)
	except (TypeError, ValueError):
		return "0"
	return str(int(value)) if value.is_integer() else f"{value:g}"


def _wrapped(value, width):
	text = _clean_text(value)
	return textwrap.wrap(
		text,
		width=max(1, width),
		break_long_words=True,
		break_on_hyphens=False,
	) or [""]


class _EscPosReceipt:
	"""Small ESC/POS writer targeting common 80 mm, 203 dpi printers."""

	def __init__(self, columns=DEFAULT_COLUMNS, encoding="cp850"):
		self.columns = columns
		self.encoding = encoding
		self.data = bytearray()

	def command(self, value):
		self.data.extend(value)

	def line(self, value="", *, align=0, bold=False, double=False):
		self.command(ESC + b"a" + bytes([align]))
		self.command(ESC + b"E" + bytes([1 if bold else 0]))
		self.command(GS + b"!" + bytes([0x11 if double else 0]))
		self.data.extend(_clean_text(value).encode(self.encoding, errors="replace"))
		self.data.extend(b"\n")

	def wrapped(self, value, *, align=0, bold=False, double=False, width=None):
		width = width or (self.columns // 2 if double else self.columns)
		for line in _wrapped(value, width):
			self.line(line, align=align, bold=bold, double=double)

	def separator(self, character="-"):
		self.line(character * self.columns)

	def pair(self, label, amount, *, bold=False):
		label = _clean_text(label)
		amount = _clean_text(amount)
		available = max(1, self.columns - len(amount) - 1)
		lines = _wrapped(label, available)
		for index, line in enumerate(lines):
			right = amount if index == len(lines) - 1 else ""
			self.line(f"{line:<{available}} {right:>{len(amount)}}", bold=bold)

	def qr(self, value):
		content = _clean_text(value).encode("utf-8")
		if not content:
			return
		self.command(ESC + b"a\x01")
		# QR model 2, module size 6 and medium error correction.
		self.command(GS + b"(k\x04\x001A2\x00")
		self.command(GS + b"(k\x03\x001C\x06")
		self.command(GS + b"(k\x03\x001E1")
		length = len(content) + 3
		self.command(GS + b"(k" + bytes([length & 0xFF, length >> 8]) + b"1P0" + content)
		self.command(GS + b"(k\x03\x001Q0")
		self.command(b"\n")

	def finish(self):
		self.command(ESC + b"E\x00" + GS + b"!\x00" + ESC + b"a\x00")
		self.command(b"\n\n\n")
		# Partial cut. Printers without a cutter normally ignore this command.
		self.command(GS + b"VB\x00")
		return bytes(self.data)


def _append_item(receipt, item, currency):
	qty_width, description_width, amount_width = 4, 27, 15
	name = _value(item, "item_name") or _value(item, "item_code")
	name_lines = _wrapped(name, description_width)
	quantity = _number(_value(item, "qty"))
	amount = _money(_value(item, "amount"), currency)
	for index, description in enumerate(name_lines):
		left = quantity if index == 0 else ""
		right = amount if index == 0 else ""
		receipt.line(
			f"{left:>{qty_width}} {description:<{description_width}} {right:>{amount_width}}",
			bold=index == 0,
		)
	code = _clean_text(_value(item, "item_code"))
	detail = []
	if code and code != _clean_text(name):
		detail.append(code)
	detail.append(f"P. unitario: {_money(_value(item, 'rate'), currency)}")
	if float(_value(item, "discount_percentage", 0) or 0):
		detail.append(f"Descuento: {_number(_value(item, 'discount_percentage'))}%")
	receipt.wrapped("  " + " | ".join(detail))


def build_pos_invoice_escpos(
	doc,
	*,
	company_tax_id=None,
	tip=None,
	copies=1,
	columns=DEFAULT_COLUMNS,
):
	"""Build a complete native ESC/POS receipt and return raw bytes."""
	currency = _value(doc, "currency", "PEN")

	def build_copy():
		receipt = _EscPosReceipt(columns=columns)
		receipt.command(ESC + b"@")
		# Epson-compatible table 2 is PC850 on common POS-80 printers.
		receipt.command(ESC + b"t\x02")
		receipt.wrapped(_value(doc, "company"), align=1, bold=True, double=True)
		if company_tax_id:
			receipt.line(f"RUC {_clean_text(company_tax_id)}", align=1, bold=True)
		if _value(doc, "company_address_display"):
			receipt.wrapped(_value(doc, "company_address_display"), align=1)
		receipt.wrapped(
			_value(doc, "tipo_comprobante") or "Comprobante electronico",
			align=1, bold=True,
		)
		receipt.line(_value(doc, "name"), align=1, bold=True, double=True)
		receipt.separator()
		posting_date = _clean_text(_value(doc, "posting_date"))
		posting_time = _clean_text(_value(doc, "posting_time"))
		receipt.wrapped(f"Fecha: {posting_date} {posting_time}".strip())
		customer = (_value(doc, "customer_boleta_name") or _value(doc, "customer_name") or _value(doc, "customer"))
		receipt.wrapped(f"Cliente: {customer}", bold=True)
		if _value(doc, "tax_id"):
			receipt.wrapped(f"Documento: {_value(doc, 'tax_id')}")
		customer_address = _value(doc, "customer_boleta_address") or _value(doc, "address_display")
		if customer_address:
			receipt.wrapped(f"Direccion: {customer_address}")
		if _value(doc, "table_description"):
			receipt.wrapped(f"Mesa: {_value(doc, 'table_description')}")
		receipt.separator()
		receipt.line(f"{'CANT':>4} {'DESCRIPCION':<27} {'IMPORTE':>15}", bold=True)
		receipt.separator()
		for item in _value(doc, "items", []) or []:
			_append_item(receipt, item, currency)
			receipt.line("." * columns)
		receipt.pair("Subtotal", _money(_value(doc, "net_total"), currency))
		if float(_value(doc, "total_taxes_and_charges", 0) or 0):
			receipt.pair("Impuestos", _money(_value(doc, "total_taxes_and_charges"), currency))
		if float(_value(doc, "discount_amount", 0) or 0):
			receipt.pair("Descuento", "-" + _money(_value(doc, "discount_amount"), currency))
		receipt.separator("=")
		receipt.pair("TOTAL", _money(_value(doc, "grand_total"), currency), bold=True)
		receipt.separator("=")
		payments = [payment for payment in (_value(doc, "payments", []) or []) if float(_value(payment, "amount", 0) or 0)]
		if payments:
			receipt.line("FORMA DE PAGO", bold=True)
			for payment in payments:
				receipt.pair(_value(payment, "mode_of_payment"), _money(_value(payment, "amount"), currency))
			if float(_value(doc, "change_amount", 0) or 0):
				receipt.pair("Vuelto", _money(_value(doc, "change_amount"), currency))
		if tip and float(_value(tip, "amount", 0) or 0):
			receipt.separator()
			receipt.pair("PROPINA NO FISCAL", _money(_value(tip, "amount"), currency), bold=True)
			receipt.wrapped(f"Cobro: {_value(tip, 'mode_of_payment')}")
		if _value(doc, "codigo_qr_sunat"):
			receipt.qr(_value(doc, "codigo_qr_sunat"))
		if _value(doc, "estado_sunat"):
			receipt.wrapped(f"Estado SUNAT: {_value(doc, 'estado_sunat')}", align=1, bold=True)
		if _value(doc, "codigo_hash_sunat"):
			receipt.wrapped(f"Hash: {_value(doc, 'codigo_hash_sunat')}", align=1)
		receipt.wrapped("Representacion impresa del comprobante electronico.", align=1)
		receipt.separator()
		receipt.line("GRACIAS POR SU PREFERENCIA!", align=1, bold=True)
		return receipt.finish()

	# WHB 0.14 ignores qty for raw jobs, so each copy is explicitly encoded.
	return b"".join(build_copy() for _ in range(max(1, int(copies or 1))))


def _consolidate_account_items(items):
	"""Consolidate equal dishes as the legacy pre-account format does."""
	consolidated = {}
	for item in items or []:
		key = (
			_clean_text(_value(item, "item_code")),
			float(_value(item, "rate", 0) or 0),
			float(_value(item, "discount_percentage", 0) or 0),
		)
		if key not in consolidated:
			consolidated[key] = {
				"item_code": _value(item, "item_code"),
				"item_name": _value(item, "item_name"),
				"qty": float(_value(item, "qty", 0) or 0),
				"rate": _value(item, "rate", 0),
				"amount": float(_value(item, "amount", 0) or 0),
				"discount_percentage": _value(item, "discount_percentage", 0),
			}
		else:
			consolidated[key]["qty"] += float(_value(item, "qty", 0) or 0)
			consolidated[key]["amount"] += float(_value(item, "amount", 0) or 0)
	return consolidated.values()


def build_table_order_account_escpos(
	doc,
	*,
	company_tax_id=None,
	waiter_name=None,
	customer_address=None,
	copies=1,
	columns=DEFAULT_COLUMNS,
):
	"""Build a non-fiscal pre-account ticket as native ESC/POS bytes."""
	currency = _value(doc, "currency", "PEN")
	amount = float(_value(doc, "amount", 0) or 0)
	discount = float(_value(doc, "discount", 0) or 0)
	discount_percent = float(_value(doc, "discount_global_percent", 0) or 0)
	if discount:
		total = amount - discount
	elif discount_percent:
		total = amount * (1 - discount_percent / 100)
	else:
		total = amount

	def build_copy():
		receipt = _EscPosReceipt(columns=columns)
		receipt.command(ESC + b"@")
		receipt.command(ESC + b"t\x02")
		receipt.wrapped(_value(doc, "company"), align=1, bold=True, double=True)
		if company_tax_id:
			receipt.line(f"RUC {_clean_text(company_tax_id)}", align=1, bold=True)
		receipt.line("PRE CUENTA", align=1, bold=True, double=True)
		receipt.line("DOCUMENTO NO FISCAL", align=1, bold=True)
		receipt.separator()
		receipt.wrapped(f"Orden: {_value(doc, 'name')}", bold=True)
		receipt.wrapped(f"Fecha: {_value(doc, 'creation')}")
		location = " - ".join(filter(None, [
			_clean_text(_value(doc, "room_description")),
			_clean_text(_value(doc, "table_description")),
		]))
		if location:
			receipt.wrapped(f"Ubicacion: {location}", bold=True)
		if _value(doc, "guest_count"):
			receipt.wrapped(f"Comensales: {_number(_value(doc, 'guest_count'))}")
		customer = _value(doc, "customer_name") or _value(doc, "customer")
		if customer:
			receipt.wrapped(f"Cliente: {customer}")
		if _value(doc, "customer_tax_id"):
			receipt.wrapped(f"Documento: {_value(doc, 'customer_tax_id')}")
		if customer_address:
			receipt.wrapped(f"Direccion: {customer_address}")
		if waiter_name:
			receipt.wrapped(f"Mozo: {waiter_name}")
		receipt.separator()
		receipt.line(f"{'CANT':>4} {'DESCRIPCION':<27} {'IMPORTE':>15}", bold=True)
		receipt.separator()
		for item in _consolidate_account_items(_value(doc, "entry_items", [])):
			_append_item(receipt, item, currency)
			receipt.line("." * columns)
		if float(_value(doc, "tax", 0) or 0):
			receipt.pair("Impuestos incluidos", _money(_value(doc, "tax"), currency))
		if discount:
			receipt.pair("Importe antes de descuento", _money(amount, currency))
			receipt.pair("Descuento", "-" + _money(discount, currency))
		elif discount_percent:
			receipt.pair("Importe antes de descuento", _money(amount, currency))
			receipt.pair("Descuento global", f"{_number(discount_percent)}%")
		receipt.separator("=")
		receipt.pair("TOTAL", _money(total, currency), bold=True)
		receipt.separator("=")
		if _value(doc, "comentario"):
			receipt.wrapped(f"Comentario: {_value(doc, 'comentario')}")
		receipt.line("")
		receipt.line("RUC / DNI: __________________________")
		receipt.line("RAZON SOCIAL: ______________________")
		receipt.line("")
		receipt.line("GRACIAS POR SU PREFERENCIA!", align=1, bold=True)
		return receipt.finish()

	return b"".join(build_copy() for _ in range(max(1, int(copies or 1))))
