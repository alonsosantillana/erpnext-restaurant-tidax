frappe.views.calendar["Restaurant Reservation"] = {
	field_map: {
		start: "reservation_from",
		end: "reservation_to",
		id: "name",
		title: "guest_name",
		status: "status",
		allDay: "all_day",
	},
	gantt: false,
	get_css_class(data) {
		return `reservation-${frappe.scrub(data.status || "pending")}`;
	},
};
