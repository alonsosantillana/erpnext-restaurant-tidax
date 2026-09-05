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

	const currency = frm.doc.company_currency || frappe.boot.sysdefaults.currency;
	const payment_rows = (frm.doc.payment_reconciliation || [])
		.map((row) => {
			const sales_amount =
				flt(row.expected_amount) -
				flt(row.opening_amount) +
				flt(row.restaurant_expense_amount);
			return `
				<tr>
					<td>${frappe.utils.escape_html(row.mode_of_payment || "")}</td>
					<td class="text-right">${format_currency(sales_amount, currency)}</td>
				</tr>`;
		})
		.join("");
	const tax_rows = (frm.doc.taxes || [])
		.map(
			(row) => `
				<tr>
					<td>${frappe.utils.escape_html(row.account_head || "")}</td>
					<td>${flt(row.rate)} %</td>
					<td class="text-right">${format_currency(row.amount, currency)}</td>
				</tr>`
		)
		.join("");
	const reconciliation_rows = (frm.doc.payment_reconciliation || [])
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

	wrapper.html(`
		<div class="restaurant-closing-summary">
			<h6 class="text-center uppercase" style="color: #8D99A6">
				${__("Sales Summary")}
			</h6>
			<table class="table table-bordered table-hover">
				<tbody>
					<tr>
						<td class="font-bold">${__("Grand Total")}</td>
						<td class="text-right">${format_currency(frm.doc.grand_total, currency)}</td>
					</tr>
					<tr>
						<td class="font-bold">${__("Net Total")}</td>
						<td class="text-right">${format_currency(frm.doc.net_total, currency)}</td>
					</tr>
					<tr>
						<td class="font-bold">${__("Total Quantity")}</td>
						<td class="text-right">${flt(frm.doc.total_quantity)}</td>
					</tr>
				</tbody>
			</table>

			<h6 class="text-center uppercase" style="color: #8D99A6">
				${__("Mode of Payments")}
			</h6>
			<table class="table table-bordered table-hover">
				<thead><tr>
					<th>${__("Mode of Payment")}</th>
					<th class="text-right">${__("Sales Amount")}</th>
				</tr></thead>
				<tbody>${payment_rows}</tbody>
			</table>

			${
				tax_rows
					? `<h6 class="text-center uppercase" style="color: #8D99A6">
						${__("Taxes")}
					</h6>
					<table class="table table-bordered table-hover">
						<thead><tr>
							<th>${__("Account")}</th>
							<th>${__("Tax Rate")}</th>
							<th class="text-right">${__("Amount")}</th>
						</tr></thead>
						<tbody>${tax_rows}</tbody>
					</table>`
					: ""
			}

			<div class="restaurant-closing-expense-summary">
				<h6 class="text-center uppercase" style="color: #8D99A6">
					${__("Conciliaci\u00f3n de caja y gastos")}
				</h6>
				<div style="overflow-x: auto">
					<table class="table table-bordered table-hover">
						<thead><tr>
							<th>${__("M\u00e9todo de pago")}</th>
							<th class="text-right">${__("Apertura")}</th>
							<th class="text-right">${__("Ventas")}</th>
							<th class="text-right">${__("Gastos")}</th>
							<th class="text-right">${__("Esperado")}</th>
							<th class="text-right">${__("Contado")}</th>
							<th class="text-right">${__("Diferencia")}</th>
						</tr></thead>
						<tbody>${reconciliation_rows}</tbody>
					</table>
				</div>
			</div>
		</div>`);
}
