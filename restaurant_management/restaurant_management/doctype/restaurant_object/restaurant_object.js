// Copyright (c) 2021, Quantum Bit Core and contributors
// For license information, please see license.txt

frappe.ui.form.on('Restaurant Object', {
	setup(frm) {
		frm.set_query('room', () => ({
			filters: {
				type: 'Room',
				company: frm.doc.company,
			},
		}));
	},
	company(frm) {
		if (frm.doc.room) frm.set_value('room', null);
	},
	refresh: function(frm) {},
});
