frappe.ui.form.on("Restaurant Reservation", {
	onload(frm) {
		if (frm.is_new() && !frm.doc.company) {
			frm.set_value("company", frappe.defaults.get_user_default("company"));
		}
	},

	setup(frm) {
		frm.set_query("pos_profile", () => ({
			filters: { company: frm.doc.company, disabled: 0 },
		}));
		frm.set_query("customer", () => ({ filters: { disabled: 0 } }));
		frm.set_query("assigned_waiter", () => ({
			query: "frappe.core.doctype.user.user.user_query",
			filters: { enabled: 1 },
		}));
		frm.set_query("restaurant_table", "reservation_tables", () => ({
			filters: { company: frm.doc.company, type: "Table" },
		}));
	},

	refresh(frm) {
		if (frappe.model.can_create("Customer")) {
			frm.add_custom_button(__("Nuevo cliente"), () => create_customer(frm));
		}
		if (frm.is_new()) return;
		if (frm.doc.status === "Pending") {
			frm.add_custom_button(__("Confirmar"), () => run_action(frm, "confirm_reservation"));
		}
		if (frm.doc.status === "Confirmed") {
			frm.add_custom_button(__("Registrar llegada"), () => run_action(frm, "mark_arrived"));
		}
		if (["Confirmed", "Arrived"].includes(frm.doc.status)) {
			frm.add_custom_button(__("Sentar y abrir orden"), async () => {
				const result = await run_action(frm, "seat_and_open_order");
				if (result?.table_order) frappe.set_route("Form", "Table Order", result.table_order);
			}, __("Acciones"));
		}
		if (["Pending", "Confirmed", "Arrived"].includes(frm.doc.status)) {
			frm.add_custom_button(__("No asistió"), () => run_action(frm, "mark_no_show"), __("Acciones"));
			frm.add_custom_button(__("Cancelar"), () => cancel_reservation(frm), __("Acciones"));
		}
	},

	async company(frm) {
		if (!frm.doc.company) return;
		const response = await frappe.db.get_value(
			"Restaurant Company Settings",
			{ company: frm.doc.company },
			["pos_profile", "reservation_default_duration_minutes"]
		);
		if (response.message?.pos_profile && !frm.doc.pos_profile) {
			await frm.set_value("pos_profile", response.message.pos_profile);
		}
	},

	async reservation_from(frm) {
		if (!frm.doc.reservation_from || frm.doc.reservation_to) return;
		const response = await frappe.db.get_value(
			"Restaurant Company Settings",
			{ company: frm.doc.company },
			"reservation_default_duration_minutes"
		);
		const minutes = cint(response.message?.reservation_default_duration_minutes || 90);
		await frm.set_value(
			"reservation_to",
			moment(frm.doc.reservation_from).add(minutes, "minutes").format("YYYY-MM-DD HH:mm:ss")
		);
	},

	async customer(frm) {
		if (!frm.doc.customer) return;
		const customer = await frappe.db.get_doc("Customer", frm.doc.customer);
		await set_customer_details(frm, customer);
	},

	reservation_tables_add(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if ((frm.doc.reservation_tables || []).length === 1) {
			frappe.model.set_value(cdt, cdn, "is_primary", 1);
		}
	},
});

function create_customer(frm) {
	frappe.prompt(
		[{
			fieldname: "tax_id",
			fieldtype: "Data",
			label: __("DNI o RUC"),
			description: __("Ingrese 8 dígitos para DNI u 11 dígitos para RUC"),
			reqd: 1,
		}],
		(values) => lookup_customer_identity(frm, values.tax_id),
		__("Nuevo cliente por DNI/RUC"),
		__("Buscar")
	);
}

async function lookup_customer_identity(frm, tax_id) {
	tax_id = String(tax_id || "").trim();
	if (!/^([0-9]{8}|[0-9]{11})$/.test(tax_id)) {
		frappe.msgprint(__("El DNI debe tener 8 dígitos y el RUC 11 dígitos"));
		return;
	}
	const response = await frappe.call({
		method: "restaurant_management.api.lookup_customer_identity",
		args: { tax_id },
		freeze: true,
		freeze_message: __("Consultando DNI/RUC"),
	});
	const result = response.message;
	if (!result) return;
	if (result.status === "existing") {
		await assign_customer(frm, result.customer, false);
		return;
	}
	if (result.status === "disabled") {
		frappe.msgprint(__("El cliente registrado con este documento está deshabilitado"));
		return;
	}
	if (result.status === "not_found") {
		frappe.msgprint(__("No se encontró información para este DNI/RUC"));
		return;
	}
	if (!result.can_create) {
		frappe.msgprint(__("No tiene permiso para crear clientes"));
		return;
	}
	frappe.confirm(
		customer_identity_preview(result.identity),
		() => create_verified_customer(frm, tax_id)
	);
}

function customer_identity_preview(identity) {
	const address = identity.registered_address || {};
	const rows = [
		[__("Tipo de documento"), identity.document_kind],
		[__("DNI o RUC"), identity.tax_id],
		[__("Nombre"), identity.party_name],
		[__("Dirección"), address.address_line1],
		[__("Distrito"), address.district],
		[__("Provincia"), address.province],
		[__("Departamento"), address.department],
	];
	const table = $("<table>").addClass("table table-bordered");
	const body = $("<tbody>").appendTo(table);
	rows.filter((row) => row[1]).forEach((row) => {
		$("<tr>").append(
			$("<th>").css("width", "32%").text(row[0]),
			$("<td>").text(row[1])
		).appendTo(body);
	});
	return $("<div>").append(
		$("<p>").text(__("Información verificada. ¿Desea crear este cliente?")),
		table
	).html();
}

async function create_verified_customer(frm, tax_id) {
	const response = await frappe.call({
		method: "restaurant_management.api.create_customer_from_identity",
		type: "POST",
		args: { tax_id },
		freeze: true,
		freeze_message: __("Creando cliente"),
	});
	if (response.message) {
		await assign_customer(frm, response.message.customer, response.message.created);
	}
}

async function assign_customer(frm, customer, created) {
	await frm.set_value("customer", customer.name);
	const customer_doc = await frappe.db.get_doc("Customer", customer.name);
	await set_customer_details(frm, customer_doc);
	frappe.show_alert({
		message: created
			? __("Cliente {0} creado y asignado", [customer.customer_name])
			: __("Cliente {0} asignado", [customer.customer_name]),
		indicator: "green",
	});
}

async function set_customer_details(frm, customer) {
	await frm.set_value({
		guest_name: customer.customer_name || customer.name,
		phone: customer.mobile_no || "",
		email: customer.email_id || "",
	});
}

frappe.ui.form.on("Restaurant Reservation Table", {
	is_primary(frm, cdt, cdn) {
		const selected = locals[cdt][cdn];
		if (!selected.is_primary) return;
		(frm.doc.reservation_tables || []).forEach((row) => {
			if (row.name !== cdn && row.is_primary) {
				frappe.model.set_value(row.doctype, row.name, "is_primary", 0);
			}
		});
	},
});

async function run_action(frm, method, args = {}) {
	const response = await frm.call(method, args);
	await frm.reload_doc();
	return response.message;
}

function cancel_reservation(frm) {
	frappe.prompt(
		[{ fieldname: "reason", fieldtype: "Small Text", label: __("Motivo"), reqd: 1 }],
		(values) => run_action(frm, "cancel_reservation", { reason: values.reason }),
		__("Cancelar reserva"),
		__("Confirmar")
	);
}
