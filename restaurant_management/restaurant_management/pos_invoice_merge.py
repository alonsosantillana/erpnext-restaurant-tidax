import frappe
from frappe import _
from frappe.utils import flt

from erpnext.accounts.doctype.pos_invoice_merge_log.pos_invoice_merge_log import (
	POSInvoiceMergeLog as ERPNextPOSInvoiceMergeLog,
)
from erpnext.accounts.utils import get_currency_precision

from restaurant_management.restaurant_management.pos_closing import _is_restaurant_pos_profile


def _sum_source_taxes(source, base=False):
	fieldname = (
		"base_tax_amount_after_discount_amount"
		if base
		else "tax_amount_after_discount_amount"
	)
	return sum(flt(tax.get(fieldname)) for tax in source.get("taxes"))


def _source_items(invoice, source_name):
	return [item for item in invoice.get("items") if item.get("pos_invoice") == source_name]


def _pick_item_for_residual(items, residual, is_return=False):
	for item in reversed(items):
		qty = flt(item.get("qty"))
		amount = flt(item.get("amount"))
		new_amount = amount + residual
		if not qty or item.get("is_free_item"):
			continue
		if is_return and amount < 0 and new_amount <= 0:
			return item
		if not is_return and amount > 0 and new_amount >= 0:
			return item
	return None


def _set_item_amount(item, amount, base_amount):
	qty = flt(item.qty)
	item.amount = amount
	item.rate = amount / qty
	item.net_amount = amount
	item.net_rate = item.rate
	item.base_amount = base_amount
	item.base_rate = base_amount / qty
	item.base_net_amount = base_amount
	item.base_net_rate = item.base_rate


def reconcile_restaurant_pos_components(invoice, sources, currency_precision=None):
	"""Make mapped POS components equal their source totals without changing taxes."""
	precision = currency_precision if currency_precision is not None else get_currency_precision()
	precision = precision or 2
	unit = 10 ** (-precision)

	for source in sources:
		items = _source_items(invoice, source.name)
		item_total = sum(flt(item.get("amount")) for item in items)
		base_item_total = sum(flt(item.get("base_amount")) for item in items)
		residual = flt(
			flt(source.get("grand_total")) - item_total - _sum_source_taxes(source),
			precision,
		)
		base_residual = flt(
			flt(source.get("base_grand_total"))
			- base_item_total
			- _sum_source_taxes(source, base=True),
			precision,
		)

		if abs(residual) > unit or abs(base_residual) > unit:
			frappe.throw(
				_(
					"La Factura POS {0} tiene una diferencia de componentes de {1}. "
					"Revise sus importes e impuestos antes de consolidar."
				).format(frappe.bold(source.name), frappe.bold(residual)),
				title=_("Diferencia no conciliable"),
			)

		if not residual and not base_residual:
			continue

		item = _pick_item_for_residual(items, residual, bool(source.get("is_return")))
		if not item:
			frappe.throw(
				_("No existe una línea elegible para conciliar la Factura POS {0}.").format(
					frappe.bold(source.name)
				),
				title=_("Diferencia no conciliable"),
			)

		_set_item_amount(
			item,
			flt(flt(item.amount) + residual, precision),
			flt(flt(item.base_amount) + base_residual, precision),
		)

	invoice.change_amount = 0
	invoice.base_change_amount = 0
	invoice.write_off_amount = 0
	invoice.base_write_off_amount = 0
	return invoice


class RestaurantPOSInvoiceMergeLog(ERPNextPOSInvoiceMergeLog):
	def merge_pos_invoice_into(self, invoice, data):
		invoice = super().merge_pos_invoice_into(invoice, data)
		if not data or not invoice.get("disable_rounded_total"):
			return invoice

		pos_profile = data[0].get("pos_profile")
		if not pos_profile or not _is_restaurant_pos_profile(pos_profile):
			return invoice

		return reconcile_restaurant_pos_components(invoice, data)
