frappe.listview_settings["Restaurant Reservation"] = {
	add_fields: ["status", "reservation_from", "guest_count"],
	get_indicator(doc) {
		const colors = {
			Pending: "orange",
			Confirmed: "blue",
			Arrived: "cyan",
			Seated: "purple",
			Completed: "green",
			"No Show": "grey",
			Cancelled: "red",
		};
		return [__(doc.status), colors[doc.status] || "grey", `status,=,${doc.status}`];
	},
};
