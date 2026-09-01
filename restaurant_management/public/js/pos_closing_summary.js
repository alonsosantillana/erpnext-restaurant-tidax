// Copyright (c) 2026, Restaurant Management contributors
// For license information, please see license.txt

frappe.ui.form.on("POS Closing Entry", {
	refresh(frm) {
		if (frm.doc.docstatus !== 1) return;
		frappe.after_ajax(() => render_restaurant_closing_summary(frm));
	},
});

function render_restaurant_closing_summary(frm) {
	const wrapper = frm.get_field("payment_reconciliation_details")?.$wrapper;
	if (!wrapper?.length) return;

	wrapper.find(".restaurant-closing-expense-summary").remove();
	const currency = frm.doc.company_currency || frappe.boot.sysdefaults.currency;
	const rows = (frm.doc.payment_reconciliation || [])
		.map(
			(row) => `
				<tr>
					<td>${frappe.utils.escape_html(row.mode_of_payment || "")}</td>
					<td class="text-right">${format_currency(row.opening_amount, currency)}</td>
					<td class="text-right">${format_currency(row.restaurant_sales_amount, currency)}</td>
					<td class="text-right">${format_currency(row.restaurant_expense_amount, currency)}</td>
					<td class="text-right">${format_currency(row.expected_amount, currency)}</td>
					<td class="text-right">${format_currency(row.closing_amount, currency)}</td>
					<td class="text-right">${format_currency(row.difference, currency)}</td>
				</tr>`
		)
		.join("");

	wrapper.append(`
		<div class="restaurant-closing-expense-summary">
			<h6 class="text-center uppercase" style="color: #8D99A6">
				${__("Conciliación de caja y gastos")}
			</h6>
			<div style="overflow-x: auto">
				<table class="table table-bordered table-hover">
					<thead><tr>
						<th>${__("Método de pago")}</th>
						<th class="text-right">${__("Apertura")}</th>
						<th class="text-right">${__("Ventas")}</th>
						<th class="text-right">${__("Gastos")}</th>
						<th class="text-right">${__("Esperado")}</th>
						<th class="text-right">${__("Contado")}</th>
						<th class="text-right">${__("Diferencia")}</th>
					</tr></thead>
					<tbody>${rows}</tbody>
				</table>
			</div>
		</div>`);
}
