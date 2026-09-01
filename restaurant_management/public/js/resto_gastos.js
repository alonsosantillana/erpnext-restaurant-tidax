const EXPENSE_CONTEXT_METHOD =
	"restaurant_management.restaurant_management.doctype.resto_gastos.resto_gastos.get_opening_context";
const EXPENSE_ACCOUNT_METHOD =
	"restaurant_management.restaurant_management.doctype.resto_gastos.resto_gastos.get_expense_account";

frappe.ui.form.on("Resto Gastos", {
	setup(frm) {
		frm._expense_modes = [];
		frm._expense_accounts = {};

		frm.set_query("pos_opening_entry", () => ({
			filters: {
				company: frm.doc.company || "",
				docstatus: 1,
				status: "Open",
			},
		}));
		frm.set_query("mode_of_payment", () => ({
			filters: [
				["Mode of Payment", "enabled", "=", 1],
				["Mode of Payment", "name", "in", frm._expense_modes.length ? frm._expense_modes : [""]],
			],
		}));
		frm.fields_dict.gto_detalle.grid.get_field("item_gto").get_query = () => ({
			filters: { item_group: "GASTOS", disabled: 0 },
		});
	},

	async onload(frm) {
		if (frm.is_new() && !frm.doc.company) {
			await frm.set_value("company", frappe.defaults.get_user_default("Company"));
		}
		if (frm.doc.pos_opening_entry) {
			await load_opening_context(frm);
		}
		await refresh_expense_accounts(frm);
	},

	async company(frm) {
		if (frm.is_new()) {
			await clear_opening_context(frm);
		}
	},

	async pos_opening_entry(frm) {
		if (!frm.doc.pos_opening_entry) {
			await clear_opening_context(frm, false);
			return;
		}
		await load_opening_context(frm);
	},

	async mode_of_payment(frm) {
		await frm.set_value(
			"payment_account",
			frm._expense_accounts[frm.doc.mode_of_payment] || null
		);
	},

	validate(frm) {
		set_expense_total(frm);
	},
});

frappe.ui.form.on("Resto Gastos Detalle", {
	async item_gto(frm, cdt, cdn) {
		await set_row_expense_account(frm, cdt, cdn);
	},

	importe_gto(frm) {
		set_expense_total(frm);
	},

	gto_detalle_remove(frm) {
		set_expense_total(frm);
	},
});

async function load_opening_context(frm) {
	const response = await frappe.call({
		method: EXPENSE_CONTEXT_METHOD,
		args: { pos_opening_entry: frm.doc.pos_opening_entry },
	});
	const context = response.message || {};
	if (frm.doc.company && context.company !== frm.doc.company) {
		await frm.set_value("pos_opening_entry", null);
		frappe.throw(__("The POS Opening Entry does not belong to the selected company"));
	}

	frm._expense_modes = context.modes_of_payment || [];
	frm._expense_accounts = context.payment_accounts || {};
	await frm.set_value("company", context.company);
	await frm.set_value("pos_profile", context.pos_profile);
	if (frm.doc.mode_of_payment && !frm._expense_modes.includes(frm.doc.mode_of_payment)) {
		await frm.set_value("mode_of_payment", null);
	}
	await frm.set_value(
		"payment_account",
		frm._expense_accounts[frm.doc.mode_of_payment] || null
	);
}

async function clear_opening_context(frm, clearOpening = true) {
	frm._expense_modes = [];
	frm._expense_accounts = {};
	if (clearOpening) {
		await frm.set_value("pos_opening_entry", null);
	}
	await frm.set_value("pos_profile", null);
	await frm.set_value("mode_of_payment", null);
	await frm.set_value("payment_account", null);
}

async function set_row_expense_account(frm, cdt, cdn) {
	const row = locals[cdt] && locals[cdt][cdn];
	if (!row) return;
	if (!row.item_gto || !frm.doc.company) {
		await frappe.model.set_value(cdt, cdn, "expense_account", null);
		return;
	}

	const item_code = row.item_gto;
	const company = frm.doc.company;
	const response = await frappe.call({
		method: EXPENSE_ACCOUNT_METHOD,
		args: { item_code, company },
	});
	const current_row = locals[cdt] && locals[cdt][cdn];
	if (
		current_row
		&& current_row.item_gto === item_code
		&& frm.doc.company === company
	) {
		await frappe.model.set_value(
			cdt,
			cdn,
			"expense_account",
			response.message || null
		);
	}
}

async function refresh_expense_accounts(frm) {
	for (const row of frm.doc.gto_detalle || []) {
		if (row.item_gto && !row.expense_account) {
			await set_row_expense_account(frm, row.doctype, row.name);
		}
	}
}

function set_expense_total(frm) {
	const total = (frm.doc.gto_detalle || []).reduce(
		(sum, row) => sum + flt(row.importe_gto),
		0
	);
	frm.set_value("gto_total", total);
}
