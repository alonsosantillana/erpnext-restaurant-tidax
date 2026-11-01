import frappe
from frappe import _
from frappe.utils import get_datetime

from erpnext.accounts.doctype.pos_closing_entry import pos_closing_entry as native_pos_closing

ERPNextPOSClosingEntry = native_pos_closing.POSClosingEntry


def erpnext_get_pos_invoices(start, end, pos_profile, user):
	"""Retain the legacy list-of-full-POS-documents response on either version."""
	legacy = getattr(native_pos_closing, "get_pos_invoices", None)
	if legacy is not None:
		return legacy(start, end, pos_profile, user)
	payload = native_pos_closing.get_invoices(start, end, pos_profile, user)
	return [frappe.get_doc("POS Invoice", row["name"]).as_dict()
		for row in payload["invoices"] if row["doctype"] == "POS Invoice"]


def _is_restaurant_pos_profile(pos_profile):
	return bool(
		frappe.db.exists(
			"Restaurant Company Settings",
			{"pos_profile": pos_profile},
		)
	)


def get_active_restaurant_opening(pos_profile, user=None, throw=False):
	filters = {
		"pos_profile": pos_profile,
		"docstatus": 1,
		"status": "Open",
	}
	openings = frappe.get_all(
		"POS Opening Entry",
		filters=filters,
		fields=["name", "company", "user", "period_start_date"],
		order_by="period_start_date desc",
	)

	if user:
		user_openings = [opening for opening in openings if opening.user == user]
		if len(user_openings) == 1:
			return user_openings[0]

	if len(openings) == 1:
		return openings[0]
	if not openings:
		if throw:
			frappe.throw(
				_("No existe una apertura POS activa para el Perfil POS {0}.").format(
					frappe.bold(pos_profile)
				)
			)
		return None

	if throw:
		frappe.throw(
			_(
				"Existen varias aperturas activas para el Perfil POS {0}. "
				"Cierre las aperturas adicionales antes de cobrar desde el restaurante."
			).format(frappe.bold(pos_profile))
		)
	return None


def assign_restaurant_pos_opening(invoice, method=None):
	if (
		not invoice.get("is_pos")
		or not invoice.get("pos_profile")
		or invoice.get("restaurant_pos_opening_entry")
		or not _is_restaurant_pos_profile(invoice.pos_profile)
	):
		return

	opening = get_active_restaurant_opening(
		invoice.pos_profile,
		user=frappe.session.user,
		throw=True,
	)
	if opening.company != invoice.company:
		frappe.throw(_("La apertura POS activa pertenece a otra compañía."))
	invoice.restaurant_pos_opening_entry = opening.name


def backfill_open_restaurant_pos_invoices():
	"""Link existing unconsolidated invoices to their single active opening."""
	if not frappe.db.has_column("POS Invoice", "restaurant_pos_opening_entry"):
		return

	profiles = frappe.get_all(
		"Restaurant Company Settings",
		filters={"pos_profile": ["is", "set"]},
		pluck="pos_profile",
	)
	for pos_profile in set(profiles):
		openings = frappe.get_all(
			"POS Opening Entry",
			filters={
				"pos_profile": pos_profile,
				"docstatus": 1,
				"status": "Open",
			},
			fields=["name", "company", "period_start_date"],
			order_by="period_start_date desc",
		)
		if len(openings) != 1:
			continue

		opening = openings[0]
		frappe.db.sql(
			"""
			update `tabPOS Invoice`
			set restaurant_pos_opening_entry = %(opening_entry)s
			where docstatus = 1
				and company = %(company)s
				and pos_profile = %(pos_profile)s
				and ifnull(length(consolidated_invoice), 0) = 0
				and ifnull(length(restaurant_pos_opening_entry), 0) = 0
				and timestamp(posting_date, posting_time) >= %(period_start_date)s
			""",
			{
				"opening_entry": opening.name,
				"company": opening.company,
				"pos_profile": pos_profile,
				"period_start_date": opening.period_start_date,
			},
		)


def _find_opening_for_closing(start, end, pos_profile, user):
	openings = frappe.get_all(
		"POS Opening Entry",
		filters={
			"pos_profile": pos_profile,
			"user": user,
			"docstatus": 1,
			"period_start_date": ["between", [start, end]],
		},
		fields=["name", "period_start_date", "status"],
		order_by="period_start_date desc",
	)
	if not openings:
		return None

	start_datetime = get_datetime(start)
	for opening in openings:
		if get_datetime(opening.period_start_date) == start_datetime:
			return opening.name
	return openings[0].name


@frappe.whitelist()
def get_pos_invoices(start, end, pos_profile, user):
	if not _is_restaurant_pos_profile(pos_profile):
		return erpnext_get_pos_invoices(start, end, pos_profile, user)

	opening_entry = _find_opening_for_closing(start, end, pos_profile, user)
	if not opening_entry:
		return erpnext_get_pos_invoices(start, end, pos_profile, user)

	rows = frappe.db.sql(
		"""
		select
			name,
			timestamp(posting_date, posting_time) as posting_datetime
		from `tabPOS Invoice`
		where docstatus = 1
			and pos_profile = %(pos_profile)s
			and ifnull(length(consolidated_invoice), 0) = 0
			and (
				restaurant_pos_opening_entry = %(opening_entry)s
				or (
					ifnull(length(restaurant_pos_opening_entry), 0) = 0
					and owner = %(user)s
				)
			)
		order by posting_datetime
		""",
		{
			"pos_profile": pos_profile,
			"opening_entry": opening_entry,
			"user": user,
		},
		as_dict=True,
	)
	start_datetime = get_datetime(start)
	end_datetime = get_datetime(end)
	rows = [
		row
		for row in rows
		if start_datetime <= get_datetime(row.posting_datetime) <= end_datetime
	]
	return [frappe.get_doc("POS Invoice", row.name).as_dict() for row in rows]


class RestaurantPOSClosingEntry(ERPNextPOSClosingEntry):
	def validate_pos_invoices(self):
		invalid_rows = []
		is_restaurant = _is_restaurant_pos_profile(self.pos_profile)

		references = self.get("pos_invoices")
		if references is None:
			references = self.get("pos_transactions", [])
		for reference in references or []:
			invoice = frappe.db.get_value(
				"POS Invoice",
				reference.pos_invoice,
				[
					"consolidated_invoice",
					"pos_profile",
					"docstatus",
					"owner",
					"restaurant_pos_opening_entry",
				],
				as_dict=True,
			)
			messages = []
			if not invoice:
				messages.append(_("La Factura POS no existe"))
			elif invoice.consolidated_invoice:
				messages.append(_("La Factura POS ya fue consolidada"))
			elif invoice.pos_profile != self.pos_profile:
				messages.append(
					_("El Perfil POS no coincide con {0}").format(frappe.bold(self.pos_profile))
				)
			elif invoice.docstatus != 1:
				messages.append(_("La Factura POS no está enviada"))
			elif is_restaurant:
				if invoice.restaurant_pos_opening_entry:
					if invoice.restaurant_pos_opening_entry != self.pos_opening_entry:
						messages.append(_("La Factura POS pertenece a otra apertura de caja"))
				elif invoice.owner != self.user:
					messages.append(_("La Factura POS no está vinculada con esta apertura de caja"))
			elif invoice.owner != self.user:
				messages.append(
					_("La Factura POS no fue creada por el usuario {0}").format(frappe.bold(self.user))
				)

			if messages:
				invalid_rows.append({"idx": reference.idx, "messages": messages})

		if invalid_rows:
			errors = []
			for row in invalid_rows:
				for message in row["messages"]:
					errors.append(_("Fila #{0}: {1}").format(row["idx"], message))
			frappe.throw(errors, title=_("Facturas POS inválidas"), as_list=True)


def _v16_pos_invoice_row(invoice):
	"""Project an already-scoped POS document onto the native v16 row contract."""
	fields = ("name", "customer", "posting_date", "grand_total", "net_total", "total_qty",
		"total_taxes_and_charges", "change_amount", "account_for_change_amount", "is_return", "return_against")
	row = frappe._dict({field: invoice.get(field) for field in fields})
	row["doctype"] = "POS Invoice"
	row["timestamp"] = get_datetime(f"{invoice.get('posting_date')} {invoice.get('posting_time')}")
	return row


@frappe.whitelist()
def get_invoices(start, end, pos_profile, user):
	"""Preserve the v16 payload and existing restaurant opening-session scope."""
	payload = native_pos_closing.get_invoices(start, end, pos_profile, user)
	if (not _is_restaurant_pos_profile(pos_profile)
		or frappe.db.get_single_value("POS Settings", "invoice_type") != "POS Invoice"):
		return payload
	# Keep native Sales Invoice rows; replace only POS rows using the existing scope.
	rows = [row for row in payload["invoices"] if row["doctype"] != "POS Invoice"]
	rows.extend(_v16_pos_invoice_row(invoice) for invoice in get_pos_invoices(start, end, pos_profile, user))
	rows.sort(key=lambda row: get_datetime(row["timestamp"]))
	return dict(payload, invoices=rows, payments=native_pos_closing.get_payments(rows),
		taxes=native_pos_closing.get_taxes(rows))
