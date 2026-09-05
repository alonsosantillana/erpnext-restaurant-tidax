from collections import defaultdict
from datetime import timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, now_datetime

from erpnext.manufacturing.doctype.bom.bom import get_bom_items
from erpnext.manufacturing.doctype.work_order.work_order import get_item_details
from erpnext.stock.get_item_details import get_default_bom
from erpnext.stock.utils import get_stock_balance


def _check_material_request_permission(ptype):
	if not frappe.has_permission("Material Request", ptype=ptype):
		frappe.throw(_("No tiene permiso para {0} Solicitudes de Material.").format(ptype), frappe.PermissionError)


def _get_production_settings(company, require_warehouses=True):
	settings_name = frappe.db.get_value("Restaurant Company Settings", {"company": company}, "name")
	if not settings_name:
		frappe.throw(_("Configure Restaurant Company Settings para {0}.").format(frappe.bold(company)))

	settings = frappe.get_cached_doc("Restaurant Company Settings", settings_name)

	if require_warehouses:
		missing = []
		for fieldname, label in (
			("raw_material_warehouse", _("Almacén de materia prima")),
			("wip_warehouse", _("Almacén en proceso")),
			("finished_goods_warehouse", _("Almacén de producto terminado")),
		):
			if not settings.get(fieldname):
				missing.append(label)
		if missing:
			frappe.throw(
				_("Complete estas configuraciones de producción en Restaurant Company Settings: {0}").format(
					", ".join(missing)
				)
			)

	return settings


def _validate_warehouse(warehouse, company, label):
	row = frappe.db.get_value("Warehouse", warehouse, ["company", "is_group", "disabled"], as_dict=True)
	if not row or row.company != company or row.is_group or row.disabled:
		frappe.throw(_("{0} debe ser un almacén activo y no agrupador de {1}.").format(label, company))


def validate_company_production_settings(doc):
	for fieldname, label in (
		("raw_material_warehouse", _("Almacén de materia prima")),
		("wip_warehouse", _("Almacén en proceso")),
		("finished_goods_warehouse", _("Almacén de producto terminado")),
	):
		if doc.get(fieldname):
			_validate_warehouse(doc.get(fieldname), doc.company, label)


def set_pos_invoice_stock_update(doc, method=None):
	"""Apply the company production policy to every restaurant POS invoice."""
	if not doc.company:
		return

	settings_name = frappe.db.get_value(
		"Restaurant Company Settings", {"company": doc.company}, "name"
	)
	if not settings_name:
		return

	update_stock = frappe.db.get_value(
		"Restaurant Company Settings", settings_name, "update_stock_on_invoice"
	)
	doc.update_stock = cint(1 if update_stock is None else update_stock)

	if doc.update_stock and not doc.set_warehouse and doc.pos_profile:
		doc.set_warehouse = frappe.db.get_value("POS Profile", doc.pos_profile, "warehouse")


def _validate_period(from_datetime, to_datetime):
	start = get_datetime(from_datetime)
	end = get_datetime(to_datetime)
	if start > end:
		frappe.throw(_("La fecha Desde no puede ser posterior a la fecha Hasta."))
	return start, end


def _get_production_timeline(sources, fallback_datetime=None):
	opening_entries = set()
	opening_datetimes = []
	consumption_datetimes = [
		get_datetime(source.get("posting_datetime"))
		for source in sources
		if source.get("posting_datetime")
	]
	missing_opening = [
		source.get("pos_invoice") or source.get("pos_invoice_item")
		for source in sources
		if not source.get("pos_opening_entry") or not source.get("opening_datetime")
	]
	if missing_opening:
		frappe.throw(
			_("Estas Facturas POS no están vinculadas correctamente a una apertura POS: {0}.").format(
				", ".join(sorted(set(missing_opening)))
			)
		)
	for source in sources:
		opening_entry = source.get("pos_opening_entry")
		opening_datetime = source.get("opening_datetime")
		if opening_entry:
			opening_entries.add(opening_entry)
		if opening_datetime:
			opening_datetimes.append(get_datetime(opening_datetime))

	if len(opening_entries) > 1:
		frappe.throw(
			_("Las ventas seleccionadas pertenecen a varias aperturas POS ({0}). Genere una solicitud por cada apertura.").format(
				", ".join(sorted(opening_entries))
			)
		)

	first_consumption = (
		min(consumption_datetimes) if consumption_datetimes else get_datetime(fallback_datetime)
	).replace(microsecond=0)
	opening_datetime = (
		min(opening_datetimes) if opening_datetimes else first_consumption
	).replace(microsecond=0)
	production_datetime = opening_datetime - timedelta(minutes=1)
	transfer_datetime = opening_datetime - timedelta(minutes=2)
	return transfer_datetime, production_datetime, first_consumption, opening_datetime


def _get_unprocessed_sales(company, pos_profile, start, end):
	return frappe.db.sql(
		"""
		select
			pii.name as pos_invoice_item,
			pii.parent as pos_invoice,
			pii.item_code,
			pii.item_name,
			pii.qty,
			pii.stock_uom,
			pi.restaurant_pos_opening_entry as pos_opening_entry,
			poe.period_start_date as opening_datetime,
			timestamp(pi.posting_date, coalesce(pi.posting_time, '00:00:00')) as posting_datetime
		from `tabPOS Invoice Item` pii
		inner join `tabPOS Invoice` pi on pi.name = pii.parent
		left join `tabPOS Opening Entry` poe on poe.name = pi.restaurant_pos_opening_entry
		where pi.docstatus = 1
			and pi.is_return = 0
			and pi.update_stock = 1
			and pi.company = %(company)s
			and pi.pos_profile = %(pos_profile)s
			and timestamp(pi.posting_date, coalesce(pi.posting_time, '00:00:00'))
				between %(start)s and %(end)s
			and pii.qty > 0
			and coalesce(pii.restaurant_material_request, '') = ''
		order by pi.posting_date, pi.posting_time, pi.name, pii.idx
		""",
		{
			"company": company,
			"pos_profile": pos_profile,
			"start": start,
			"end": end,
		},
		as_dict=True,
	)


def _get_valid_bom(item_code, company, throw=True):
	bom_no = get_default_bom(item_code)
	if not bom_no:
		if throw:
			frappe.throw(
				_("El producto {0} no tiene un BOM activo y predeterminado.").format(
					frappe.bold(item_code)
				)
			)
		return None

	bom_company = frappe.db.get_value("BOM", bom_no, "company")
	if bom_company and bom_company != company:
		frappe.throw(
			_("El BOM {0} del producto {1} pertenece a otra compañía.").format(
				frappe.bold(bom_no), frappe.bold(item_code)
			)
		)
	return bom_no


def _build_preview(company, sales, settings):
	grouped = defaultdict(lambda: {"qty": 0.0, "sources": [], "invoices": set()})
	for source in sales:
		row = grouped[source.item_code]
		row["qty"] += flt(source.qty)
		row["sources"].append(source)
		row["invoices"].add(source.pos_invoice)

	production_items = []
	production_sources = []
	skipped_items = []
	material_totals = defaultdict(lambda: {"qty": 0.0, "stock_uom": None})
	for item_code in sorted(grouped):
		group = grouped[item_code]
		item = frappe.db.get_value(
			"Item", item_code, ["item_name", "description", "stock_uom"], as_dict=True
		)
		if not item:
			frappe.throw(_("No existe el producto {0}.").format(frappe.bold(item_code)))

		bom_no = _get_valid_bom(item_code, company, throw=False)
		if not bom_no:
			skipped_items.append(
				{
					"item_code": item_code,
					"item_name": item.item_name,
					"qty": group["qty"],
					"reason": _("Sin BOM activo y predeterminado"),
				}
			)
			continue

		for material in get_bom_items(bom_no, company, qty=group["qty"], fetch_exploded=1):
			material_totals[material.item_code]["qty"] += flt(material.qty)
			material_totals[material.item_code]["stock_uom"] = material.stock_uom

		production_sources.extend(group["sources"])
		production_items.append(
			{
				"item_code": item_code,
				"item_name": item.item_name,
				"description": item.description or item.item_name,
				"qty": group["qty"],
				"uom": item.stock_uom,
				"stock_uom": item.stock_uom,
				"conversion_factor": 1,
				"bom_no": bom_no,
				"warehouse": settings.finished_goods_warehouse,
				"pos_invoice": " / ".join(sorted(group["invoices"])),
				"source_count": len(group["sources"]),
			}
		)

	transfer_datetime = (
		_get_production_timeline(production_sources, now_datetime())[0]
		if production_sources
		else None
	)
	materials = []
	for item_code in sorted(material_totals):
		material = material_totals[item_code]
		available_qty = flt(
			get_stock_balance(
				item_code,
				settings.raw_material_warehouse,
				transfer_datetime.date(),
				transfer_datetime.time(),
			)
		)
		materials.append(
			{
				"item_code": item_code,
				"item_name": frappe.db.get_value("Item", item_code, "item_name"),
				"required_qty": material["qty"],
				"available_qty": available_qty,
				"shortage_qty": max(material["qty"] - available_qty, 0),
				"stock_uom": material["stock_uom"],
			}
		)

	return production_items, materials, production_sources, skipped_items


@frappe.whitelist()
def get_restaurant_production_defaults(company):
	_check_material_request_permission("create")
	settings = _get_production_settings(company)
	return {
		"raw_material_warehouse": settings.raw_material_warehouse,
		"wip_warehouse": settings.wip_warehouse,
		"finished_goods_warehouse": settings.finished_goods_warehouse,
		"pos_profile": settings.pos_profile,
	}


@frappe.whitelist()
def get_restaurant_production_preview(company, pos_profile, from_datetime, to_datetime):
	_check_material_request_permission("create")
	start, end = _validate_period(from_datetime, to_datetime)
	settings = _get_production_settings(company)

	profile = frappe.db.get_value("POS Profile", pos_profile, ["company", "disabled"], as_dict=True)
	if not profile or profile.company != company or profile.disabled:
		frappe.throw(_("Seleccione un Perfil POS activo de la compañía {0}.").format(company))

	sales = _get_unprocessed_sales(company, pos_profile, start, end)
	production_items, materials, production_sources, skipped_items = _build_preview(
		company, sales, settings
	)
	if production_sources:
		transfer_datetime, production_datetime, first_consumption, opening_datetime = _get_production_timeline(
			production_sources, start
		)
	else:
		transfer_datetime = production_datetime = first_consumption = opening_datetime = None
	return {
		"production_items": production_items,
		"materials": materials,
		"sources": production_sources,
		"skipped_items": skipped_items,
		"raw_material_warehouse": settings.raw_material_warehouse,
		"wip_warehouse": settings.wip_warehouse,
		"finished_goods_warehouse": settings.finished_goods_warehouse,
		"from_datetime": start,
		"to_datetime": end,
		"transfer_datetime": transfer_datetime,
		"production_datetime": production_datetime,
		"first_consumption_datetime": first_consumption,
		"opening_datetime": opening_datetime,
	}


def _get_locked_source_rows(source_names):
	if not source_names:
		return []
	return frappe.db.sql(
		"""
		select
			pii.name as pos_invoice_item,
			pii.parent as pos_invoice,
			pii.item_code,
			pii.qty,
			pii.stock_uom,
			pii.restaurant_material_request,
			pi.company,
			pi.pos_profile,
			pi.docstatus,
			pi.is_return,
			pi.update_stock,
			pi.restaurant_pos_opening_entry as pos_opening_entry,
			poe.period_start_date as opening_datetime
		from `tabPOS Invoice Item` pii
		inner join `tabPOS Invoice` pi on pi.name = pii.parent
		left join `tabPOS Opening Entry` poe on poe.name = pi.restaurant_pos_opening_entry
		where pii.name in %(source_names)s
		for update
		""",
		{"source_names": tuple(source_names)},
		as_dict=True,
	)


def validate_restaurant_production_material_request(doc, method=None):
	if not cint(doc.get("restaurant_production")):
		return

	if doc.material_request_type != "Manufacture":
		frappe.throw(_("La Solicitud de Material de Resto debe tener el propósito Manufacture."))

	settings = _get_production_settings(doc.company)
	if doc.restaurant_pos_profile and frappe.db.get_value("POS Profile", doc.restaurant_pos_profile, "company") != doc.company:
		frappe.throw(_("El Perfil POS de producción pertenece a otra compañía."))

	sources = doc.get("restaurant_production_sources") or []
	if not sources:
		frappe.throw(_("La solicitud no contiene líneas de Factura POS para producir."))

	source_names = [row.pos_invoice_item for row in sources]
	if len(source_names) != len(set(source_names)):
		frappe.throw(_("La solicitud contiene líneas de venta duplicadas."))

	database_rows = _get_locked_source_rows(source_names)
	if len(database_rows) != len(source_names):
		frappe.throw(_("Una o más líneas de Factura POS ya no existen."))

	actual_by_name = {row.pos_invoice_item: row for row in database_rows}
	expected_qty = defaultdict(float)
	opening_entries = set()
	for source in sources:
		actual = actual_by_name[source.pos_invoice_item]
		if actual.docstatus != 1 or actual.is_return or not actual.update_stock or actual.company != doc.company:
			frappe.throw(_("La línea {0} no corresponde a una venta válida de la compañía.").format(source.pos_invoice_item))
		if doc.restaurant_pos_profile and actual.pos_profile != doc.restaurant_pos_profile:
			frappe.throw(_("La línea {0} pertenece a otro Perfil POS.").format(source.pos_invoice_item))
		if actual.restaurant_material_request and actual.restaurant_material_request != doc.name:
			frappe.throw(
				_("La línea {0} ya fue incluida en {1}.").format(
					source.pos_invoice_item, frappe.bold(actual.restaurant_material_request)
				)
			)
		if flt(actual.qty) <= 0:
			frappe.throw(_("La línea {0} no es un producto vendido válido.").format(source.pos_invoice_item))
		_get_valid_bom(actual.item_code, doc.company)
		if source.item_code != actual.item_code or abs(flt(source.qty) - flt(actual.qty)) > 0.000001:
			frappe.throw(_("La trazabilidad de la línea {0} fue modificada.").format(source.pos_invoice_item))
		if not actual.pos_opening_entry or not actual.opening_datetime:
			frappe.throw(
				_("La Factura POS {0} no está vinculada a una apertura POS. Corrija el vínculo antes de producir.").format(
					frappe.bold(actual.pos_invoice)
				)
			)
		opening_entries.add(actual.pos_opening_entry)
		source.pos_opening_entry = actual.pos_opening_entry
		source.opening_datetime = actual.opening_datetime
		expected_qty[actual.item_code] += flt(actual.qty)

	if len(opening_entries) > 1:
		frappe.throw(
			_("La solicitud contiene ventas de varias aperturas POS ({0}). Genere una solicitud por cada apertura.").format(
				", ".join(sorted(opening_entries))
			)
		)

	request_items = {}
	for item in doc.items:
		if item.item_code in request_items:
			frappe.throw(_("Agrupe el producto {0} en una sola fila.").format(frappe.bold(item.item_code)))
		request_items[item.item_code] = item

	if set(request_items) != set(expected_qty):
		frappe.throw(_("Los productos de la solicitud no coinciden con las líneas de venta seleccionadas."))

	for item_code, expected in expected_qty.items():
		item = request_items[item_code]
		if abs(flt(item.qty) - expected) > 0.000001:
			frappe.throw(_("La cantidad de {0} debe ser {1}.").format(frappe.bold(item_code), expected))
		if item.warehouse != settings.finished_goods_warehouse:
			frappe.throw(
				_("El almacén destino de {0} debe ser {1}.").format(
					frappe.bold(item_code), frappe.bold(settings.finished_goods_warehouse)
				)
			)
		if item.bom_no != _get_valid_bom(item_code, doc.company):
			frappe.throw(_("El BOM del producto {0} no es el BOM predeterminado activo.").format(item_code))


def claim_restaurant_production_sources(doc, method=None):
	if not cint(doc.get("restaurant_production")):
		return
	validate_restaurant_production_material_request(doc)
	request_items = {item.item_code: item.name for item in doc.items}
	for source in doc.restaurant_production_sources:
		frappe.db.set_value(
			"POS Invoice Item",
			source.pos_invoice_item,
			{
				"restaurant_material_request": doc.name,
				"restaurant_material_request_item": request_items[source.item_code],
			},
			update_modified=False,
		)


def release_restaurant_production_sources(doc, method=None):
	if not cint(doc.get("restaurant_production")):
		return
	for source in doc.get("restaurant_production_sources") or []:
		if frappe.db.get_value("POS Invoice Item", source.pos_invoice_item, "restaurant_material_request") == doc.name:
			frappe.db.set_value(
				"POS Invoice Item",
				source.pos_invoice_item,
				{"restaurant_material_request": None, "restaurant_material_request_item": None},
				update_modified=False,
			)


@frappe.whitelist()
def create_restaurant_work_orders(material_request):
	request = frappe.get_doc("Material Request", material_request)
	request.check_permission("read")
	if not frappe.has_permission("Work Order", ptype="create"):
		frappe.throw(_("No tiene permiso para crear Órdenes de Producción."), frappe.PermissionError)
	if request.docstatus != 1 or not cint(request.get("restaurant_production")):
		frappe.throw(_("Seleccione una Solicitud de Material de Resto enviada."))

	validate_restaurant_production_material_request(request)
	settings = _get_production_settings(request.company)
	production_datetime = _get_production_timeline(
		request.restaurant_production_sources,
		request.restaurant_from_datetime or request.transaction_date,
	)[1]
	created = []
	for item in request.items:
		already_created = flt(
			frappe.db.sql(
				"""
				select coalesce(sum(qty), 0)
				from `tabWork Order`
				where docstatus < 2 and material_request_item = %s
				""",
				item.name,
			)[0][0]
		)
		qty = flt(item.stock_qty) - already_created
		if qty <= 0:
			continue

		details = get_item_details(item.item_code, project=item.project, throw=True)
		work_order = frappe.new_doc("Work Order")
		work_order.update(
			{
				"production_item": item.item_code,
				"qty": qty,
				"fg_warehouse": settings.finished_goods_warehouse,
				"wip_warehouse": settings.wip_warehouse,
				"source_warehouse": settings.raw_material_warehouse,
				"description": item.description,
				"stock_uom": item.stock_uom,
				"expected_delivery_date": production_datetime.date(),
				"bom_no": item.bom_no or details.bom_no,
				"material_request": request.name,
				"material_request_item": item.name,
				"planned_start_date": production_datetime,
				"company": request.company,
				"project": item.project,
			}
		)
		work_order.get_items_and_operations_from_bom()
		work_order.save()
		created.append(work_order.name)

	return {"work_orders": created}


def _check_fast_production_permissions():
	for doctype in ("Work Order", "Stock Entry"):
		for ptype in ("create", "submit"):
			if not frappe.has_permission(doctype, ptype=ptype):
				frappe.throw(
					_("No tiene permiso para {0} {1}.").format(ptype, doctype),
					frappe.PermissionError,
				)


def _make_and_submit_stock_entry(work_order, purpose, qty, posting_datetime):
	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	stock_entry = frappe.get_doc(make_stock_entry(work_order.name, purpose, qty))
	stock_entry.set_posting_time = 1
	stock_entry.posting_date = posting_datetime.date()
	stock_entry.posting_time = posting_datetime.time()
	stock_entry.insert()
	stock_entry.submit()
	return stock_entry.name


@frappe.whitelist()
def process_restaurant_production(material_request):
	request = frappe.get_doc("Material Request", material_request)
	request.check_permission("read")
	_check_fast_production_permissions()
	if request.docstatus != 1 or not cint(request.get("restaurant_production")):
		frappe.throw(_("Seleccione una Solicitud de Material de Resto enviada."))

	validate_restaurant_production_material_request(request)
	transfer_datetime, production_datetime, first_consumption, opening_datetime = _get_production_timeline(
		request.restaurant_production_sources,
		request.restaurant_from_datetime or request.transaction_date,
	)
	create_restaurant_work_orders(request.name)
	work_order_names = frappe.get_all(
		"Work Order",
		filters=dict(material_request=request.name, docstatus=["<", 2]),
		pluck="name",
		order_by="creation, name",
	)

	work_orders = [frappe.get_doc("Work Order", name) for name in work_order_names]
	for work_order in work_orders:
		if work_order.operations and flt(work_order.qty) > flt(work_order.produced_qty):
			frappe.throw(
				_("La Orden de Producción {0} tiene operaciones. Procésela manualmente mediante Job Cards.").format(
					frappe.bold(work_order.name)
				)
			)

	stock_entries = []
	processed_work_orders = []
	for work_order in work_orders:
		remaining_qty = flt(work_order.qty) - flt(work_order.produced_qty)
		if remaining_qty <= 0:
			continue

		if work_order.docstatus == 0:
			work_order.planned_start_date = production_datetime
			work_order.expected_delivery_date = production_datetime.date()
			work_order.save()
			work_order.submit()

		work_order.reload()
		if not cint(work_order.skip_transfer):
			pending_transfer_qty = flt(work_order.qty) - flt(
				work_order.material_transferred_for_manufacturing
			)
			if pending_transfer_qty > 0:
				stock_entries.append(
					_make_and_submit_stock_entry(
						work_order,
						"Material Transfer for Manufacture",
						pending_transfer_qty,
						transfer_datetime,
					)
				)
				work_order.reload()

		remaining_qty = flt(work_order.qty) - flt(work_order.produced_qty)
		if remaining_qty > 0:
			stock_entries.append(
				_make_and_submit_stock_entry(
					work_order,
					"Manufacture",
					remaining_qty,
					production_datetime,
				)
			)
			processed_work_orders.append(work_order.name)

	return dict(
		work_orders=work_order_names,
		processed_work_orders=processed_work_orders,
		stock_entries=stock_entries,
		transfer_datetime=transfer_datetime,
		production_datetime=production_datetime,
		first_consumption_datetime=first_consumption,
		opening_datetime=opening_datetime,
	)
