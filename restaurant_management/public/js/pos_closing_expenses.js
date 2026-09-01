// Copyright (c) 2026, Restaurant Management contributors
// For license information, please see license.txt

const RESTAURANT_CLOSING_EXPENSE_METHOD =
	"restaurant_management.restaurant_management.pos_closing_expenses.get_closing_expense_summary";

frappe.ui.form.on("POS Closing Entry", {
	refresh(frm) {
		if (!frm.doc.pos_opening_entry) return;

		frm.add_custom_button(__("Ver gastos"), () => {
			frappe.set_route("List", "Resto Gastos", {
				pos_opening_entry: ["=", frm.doc.pos_opening_entry],
			});
		});

		if (frm.doc.docstatus === 0) {
			frappe.after_ajax(() => refresh_restaurant_closing_expenses(frm));
		}
	},

	pos_opening_entry(frm) {
		if (frm.doc.docstatus !== 0 || !frm.doc.pos_opening_entry) return;
		frappe.after_ajax(() => refresh_restaurant_closing_expenses(frm));
	},

	async before_save(frm) {
		await refresh_restaurant_closing_expenses(frm);
	},
});

async function refresh_restaurant_closing_expenses(frm) {
	const opening_entry = frm.doc.pos_opening_entry;
	if (!opening_entry || frm.doc.docstatus !== 0) return;

	const response = await frappe.call({
		method: RESTAURANT_CLOSING_EXPENSE_METHOD,
		args: { pos_opening_entry: opening_entry },
	});
	if (!response.message || opening_entry !== frm.doc.pos_opening_entry) return;

	const summary = response.message;
	const expenses_by_mode = summary.by_mode_of_payment || {};
	let changed = false;

	for (const row of frm.doc.payment_reconciliation || []) {
		const previous_expense = flt(row.restaurant_expense_amount);
		const previous_sales = flt(row.restaurant_sales_amount);
		const previous_expected = flt(row.expected_amount);
		const previous_net = flt(row.opening_amount) + previous_sales - previous_expense;
		const gross_expected = amounts_are_equal(previous_expected, previous_net)
			? previous_expected + previous_expense
			: previous_expected;
		const current_expense = flt(expenses_by_mode[row.mode_of_payment]);
		const current_sales = gross_expected - flt(row.opening_amount);
		const current_expected = gross_expected - current_expense;
		const follows_expected =
			amounts_are_equal(row.closing_amount, previous_expected);
		const current_closing = follows_expected ? current_expected : flt(row.closing_amount);
		const current_difference = current_closing - current_expected;

		changed = set_if_changed(row, "restaurant_sales_amount", current_sales) || changed;
		changed = set_if_changed(row, "restaurant_expense_amount", current_expense) || changed;
		changed = set_if_changed(row, "expected_amount", current_expected) || changed;
		changed = set_if_changed(row, "closing_amount", current_closing) || changed;
		changed = set_if_changed(row, "difference", current_difference) || changed;
	}

	changed = set_if_changed(frm.doc, "restaurant_expense_total", flt(summary.total)) || changed;
	frm.refresh_field("payment_reconciliation");
	frm.refresh_field("restaurant_expense_total");
	if (changed) frm.dirty();

	if (summary.draft_count) {
		frm.set_intro(
			__("Hay {0} gastos en borrador por {1}. Debe enviarlos o eliminarlos antes de cerrar.", [
				summary.draft_count,
				format_currency(summary.draft_total, frm.doc.company_currency),
			]),
			"orange"
		);
	}
}

function amounts_are_equal(first, second) {
	return Math.abs(flt(first) - flt(second)) < 0.005;
}

function set_if_changed(target, fieldname, value) {
	if (amounts_are_equal(target[fieldname], value)) return false;
	target[fieldname] = flt(value);
	return true;
}
