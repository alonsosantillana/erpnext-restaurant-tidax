// Copyright (c) 2026, Restaurant Management contributors
// For license information, please see license.txt

async function update_restaurant_pos_series(frm) {
	if (!frm.doc.company || frm.doc.docstatus !== 0) {
		return;
	}

	const response = await frappe.call({
		method: "restaurant_management.restaurant_management.pos_series.get_pos_document_series",
		args: {
			company: frm.doc.company,
			document_type: frm.doctype,
		},
	});

	if (response.message !== frm.doc.restaurant_naming_series) {
		await frm.set_value("restaurant_naming_series", response.message);
	}
}

frappe.ui.form.on("POS Opening Entry", {
	refresh: update_restaurant_pos_series,
	company: update_restaurant_pos_series,
});

frappe.ui.form.on("POS Closing Entry", {
	refresh: update_restaurant_pos_series,
	company: update_restaurant_pos_series,

	async pos_opening_entry(frm) {
		if (!frm.doc.pos_opening_entry) {
			return;
		}

		const response = await frappe.db.get_value(
			"POS Opening Entry",
			frm.doc.pos_opening_entry,
			"company"
		);
		if (response.message?.company && response.message.company !== frm.doc.company) {
			await frm.set_value("company", response.message.company);
		}
		await update_restaurant_pos_series(frm);
	},
});
