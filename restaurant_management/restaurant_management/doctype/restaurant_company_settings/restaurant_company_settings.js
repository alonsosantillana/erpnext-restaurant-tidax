// Copyright (c) 2026, Restaurant Management contributors
// For license information, please see license.txt

frappe.ui.form.on("Restaurant Company Settings", {
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
