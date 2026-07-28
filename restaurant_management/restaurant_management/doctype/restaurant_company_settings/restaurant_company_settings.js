// Copyright (c) 2026, Restaurant Management contributors
// For license information, please see license.txt

frappe.ui.form.on("Restaurant Company Settings", {
	async company(frm) {
		if (!frm.doc.company || (!frm.is_new() && frm.doc.pos_opening_series)) {
			return;
		}

		const response = await frappe.db.get_value(
			"Company",
			frm.doc.company,
			"abbr"
		);
		const abbr = (response.message?.abbr || "")
			.toUpperCase()
			.replace(/[^A-Z0-9-]+/g, "-")
			.replace(/^-|-$/g, "");
		if (!abbr) {
			return;
		}
		if (!frm.doc.pos_opening_series) {
			await frm.set_value(
				"pos_opening_series",
				`POS-OPE-${abbr}-.YYYY.-.#####`
			);
		}
		if (!frm.doc.pos_closing_series) {
			await frm.set_value(
				"pos_closing_series",
				`POS-CLO-${abbr}-.YYYY.-.#####`
			);
		}
	},

	setup(frm) {
		frm.set_query("pos_profile", () => ({
			filters: { company: frm.doc.company, disabled: 0 },
		}));
		frm.set_query("print_format", () => ({
			filters: { doc_type: "Table Order", disabled: 0 },
		}));
		frm.set_query("print_format_order", () => ({
			filters: { doc_type: "Table Order", disabled: 0 },
		}));
		frm.set_query("print_format_ce", () => ({
			filters: { doc_type: "POS Invoice", disabled: 0 },
		}));
		frm.set_query("delivery_fee_item", () => ({
			filters: { disabled: 0, is_sales_item: 1 },
		}));
	},

	refresh(frm) {
		const permissionMessage = __(
			"Restaurant permissions apply only to this company and its permitted rooms."
		);
		frm.fields_dict.restaurant_permissions_info.$wrapper
			.empty()
			.append(permissionMessage);

		const clickMessage = __(
			"This option changes double-click actions to a single click for this company."
		);
		frm.fields_dict.double_click_events_info.$wrapper
			.empty()
			.append(clickMessage);
	},
});
