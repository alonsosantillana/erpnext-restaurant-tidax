const RESTAURANT_PRODUCTION_METHOD =
	"restaurant_management.restaurant_management.production";

frappe.ui.form.on("Material Request", {
	refresh(frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(
				__("Consumos de Resto"),
				() => open_restaurant_production_dialog(frm),
				__("Get Items From")
			);
		}

		if (frm.doc.docstatus === 1 && frm.doc.restaurant_production) {
			frm.remove_custom_button(__("Work Order"), __("Create"));
			frm.add_custom_button(
				__("Procesar producción"),
				() => process_restaurant_production(frm)
			);
			frm.change_custom_button_type(__("Procesar producción"), null, "primary");
		}
	},

	clear_item_no_manufacturing(frm) {
		show_material_preview(frm.__restaurant_production_preview || { materials: [] });
	},
});

async function open_restaurant_production_dialog(frm) {
	if (!frm.doc.company) {
		frappe.msgprint(__("Seleccione primero la compañía."));
		return;
	}

	const defaultsResponse = await frappe.call({
		method: RESTAURANT_PRODUCTION_METHOD + ".get_restaurant_production_defaults",
		args: { company: frm.doc.company },
		freeze: true,
		freeze_message: __("Validando configuración de producción..."),
	});
	const defaults = defaultsResponse.message || {};
	const start = frappe.datetime.get_today() + " 00:00:00";
	const end = frappe.datetime.now_datetime();
	const dialog = new frappe.ui.Dialog({
		title: __("Traer productos vendidos"),
		fields: [
			{
				fieldname: "company",
				fieldtype: "Link",
				options: "Company",
				label: __("Compañía"),
				default: frm.doc.company,
				reqd: 1,
				read_only: 1,
			},
			{
				fieldname: "pos_profile",
				fieldtype: "Link",
				options: "POS Profile",
				label: __("Perfil POS"),
				default: defaults.pos_profile,
				reqd: 1,
				get_query: () => ({ filters: { company: frm.doc.company, disabled: 0 } }),
			},
			{ fieldname: "period_column", fieldtype: "Column Break" },
			{
				fieldname: "from_datetime",
				fieldtype: "Datetime",
				label: __("Desde"),
				default: start,
				reqd: 1,
			},
			{
				fieldname: "to_datetime",
				fieldtype: "Datetime",
				label: __("Hasta"),
				default: end,
				reqd: 1,
			},
		],
		primary_action_label: __("Traer y agrupar"),
		async primary_action(values) {
			const response = await frappe.call({
				method: RESTAURANT_PRODUCTION_METHOD + ".get_restaurant_production_preview",
				args: values,
				freeze: true,
				freeze_message: __("Consolidando productos y explotando BOM..."),
			});
			const preview = response.message || {};
			if (!(preview.production_items || []).length) {
				if ((preview.skipped_items || []).length) {
					show_material_preview(preview);
				} else {
					frappe.msgprint(__("No hay productos vendidos pendientes de producción en el período seleccionado. Solo se incluyen Facturas POS enviadas con actualización de inventario."));
				}
				return;
			}
			await apply_restaurant_production(frm, values, preview);
			dialog.hide();
			show_material_preview(preview, frm);
		},
	});
	dialog.show();
}

async function apply_restaurant_production(frm, values, preview) {
	await frm.set_value("material_request_type", "Manufacture");
	await frm.set_value("schedule_date", frappe.datetime.get_today());
	await frm.set_value("set_warehouse", preview.finished_goods_warehouse);
	await frm.set_value("restaurant_production", 1);
	await frm.set_value("restaurant_pos_profile", values.pos_profile);
	await frm.set_value("restaurant_from_datetime", preview.from_datetime);
	await frm.set_value("restaurant_to_datetime", preview.to_datetime);
	await frm.set_value("restaurant_raw_material_warehouse", preview.raw_material_warehouse);
	await frm.set_value("restaurant_wip_warehouse", preview.wip_warehouse);

	frm.clear_table("items");
	(preview.production_items || []).forEach((item) => {
		const row = frm.add_child("items");
		Object.assign(row, {
			item_code: item.item_code,
			item_name: item.item_name,
			description: item.description,
			qty: item.qty,
			stock_qty: item.qty,
			uom: item.uom,
			stock_uom: item.stock_uom,
			conversion_factor: item.conversion_factor,
			warehouse: item.warehouse,
			schedule_date: frappe.datetime.get_today(),
			bom_no: item.bom_no,
			pos_invoice: item.pos_invoice,
		});
	});

	frm.clear_table("restaurant_production_sources");
	(preview.sources || []).forEach((source) => {
		const row = frm.add_child("restaurant_production_sources");
		Object.assign(row, source);
	});

	frm.__restaurant_production_preview = preview;
	frm.refresh_fields();
	frm.dirty();
}

function show_material_preview(preview, frm = null) {
	const materials = preview.materials || [];
	const skippedItems = preview.skipped_items || [];
	if (!materials.length && !skippedItems.length) {
		frappe.msgprint(__("Primero use Get Items From > Consumos de Resto."));
		return;
	}

	const materialRows = materials.map((item) => {
		const shortage = flt(item.shortage_qty);
		const shortageClass = shortage > 0 ? "text-danger" : "text-success";
		return `<tr>
			<td>${frappe.utils.escape_html(item.item_code)}</td>
			<td>${frappe.utils.escape_html(item.item_name || "")}</td>
			<td class="text-right">${format_number(item.required_qty)}</td>
			<td class="text-right">${format_number(item.available_qty)}</td>
			<td class="text-right ${shortageClass}">${format_number(shortage)}</td>
			<td>${frappe.utils.escape_html(item.stock_uom || "")}</td>
		</tr>`;
	}).join("");
	const materialSection = materials.length
		? `<h6>${__("Materia prima requerida")}</h6>
			<div class="table-responsive"><table class="table table-bordered table-sm">
			<thead><tr><th>${__("Código")}</th><th>${__("Materia prima")}</th><th>${__("Requerido")}</th><th>${__("Disponible")}</th><th>${__("Faltante")}</th><th>${__("UOM")}</th></tr></thead>
			<tbody>${materialRows}</tbody></table></div>`
		: "";

	const skippedRows = skippedItems.map((item) => `<tr>
		<td>${frappe.utils.escape_html(item.item_code)}</td>
		<td>${frappe.utils.escape_html(item.item_name || "")}</td>
		<td class="text-right">${format_number(item.qty)}</td>
		<td>${frappe.utils.escape_html(item.reason || "")}</td>
	</tr>`).join("");
	const skippedSection = skippedItems.length
		? `<h6 class="text-muted">${__("Productos omitidos")}</h6>
			<p class="text-muted">${__("No se marcarán como procesados. Si configura un BOM activo y predeterminado, podrán incluirse posteriormente.")}</p>
			<div class="table-responsive"><table class="table table-bordered table-sm">
			<thead><tr><th>${__("Código")}</th><th>${__("Producto")}</th><th>${__("Cantidad")}</th><th>${__("Motivo")}</th></tr></thead>
			<tbody>${skippedRows}</tbody></table></div>`
		: "";

	const openingTime = preview.opening_datetime
		? frappe.datetime.str_to_user(preview.opening_datetime)
		: "";
	const transferTime = preview.transfer_datetime
		? frappe.datetime.str_to_user(preview.transfer_datetime)
		: "";
	const productionTime = preview.production_datetime
		? frappe.datetime.str_to_user(preview.production_datetime)
		: "";
	const firstConsumption = preview.first_consumption_datetime
		? frappe.datetime.str_to_user(preview.first_consumption_datetime)
		: "";
	const timelineSection = productionTime
		? `<div class="alert alert-info">${__("Apertura de caja: {0}. Traslado de materia prima: {1}. Producción: {2}. Primer consumo registrado: {3}.", [openingTime, transferTime, productionTime, firstConsumption])}</div>`
		: "";

	const message = {
		title: __("Vista previa de producción"),
		wide: true,
		message: `<p>${__("Solo los productos vendidos con un BOM activo y predeterminado se incluyen en la solicitud. El consumo real se ejecutará desde las Órdenes de Producción.")}</p>
			${timelineSection}${materialSection}${skippedSection}`,
	};
	if (frm) {
		message.primary_action = {
			label: __("Guardar y enviar solicitud"),
			action: async () => {
				frappe.hide_msgprint();
				await frm.savesubmit();
			},
		};
	}
	frappe.msgprint(message);
}

async function process_restaurant_production(frm) {
	const response = await frappe.call({
		method: RESTAURANT_PRODUCTION_METHOD + ".process_restaurant_production",
		args: { material_request: frm.doc.name },
		freeze: true,
		freeze_message: __("Procesando órdenes e inventario..."),
	});
	const result = response.message || {};
	const workOrders = result.work_orders || [];
	const stockEntries = result.stock_entries || [];
	if (!stockEntries.length) {
		frappe.msgprint(__("Esta solicitud ya fue procesada completamente."));
		await frm.reload_doc();
		return;
	}

	const workOrderLinks = workOrders.map((name) =>
		`<a href="/app/work-order/${encodeURIComponent(name)}">${frappe.utils.escape_html(name)}</a>`
	).join(", ");
	const stockEntryLinks = stockEntries.map((name) =>
		`<a href="/app/stock-entry/${encodeURIComponent(name)}">${frappe.utils.escape_html(name)}</a>`
	).join(", ");
	const openingTime = frappe.datetime.str_to_user(result.opening_datetime);
	const productionTime = frappe.datetime.str_to_user(result.production_datetime);
	frappe.msgprint({
		title: __("Producción procesada"),
		indicator: "green",
		message: `<p>${__("La producción se contabilizó el {0}, antes de la apertura de caja del {1}.", [productionTime, openingTime])}</p>
			<p><strong>${__("Órdenes de Producción")}:</strong> ${workOrderLinks}</p>
			<p><strong>${__("Movimientos de inventario")}:</strong> ${stockEntryLinks}</p>`,
	});
	await frm.reload_doc();
}
