frappe.listview_settings["Material Request"] = {
	has_indicator_for_draft: true,
	has_indicator_for_cancelled: true,
	get_indicator: function (doc) {
		if (doc.status === "Pending Approval") {
			return [__("Pending Approval"), "blue", "status,=,Pending Approval"];
		} else if (doc.status === "Under Review") {
			return [__("Under Review"), "orange", "status,=,Under Review"];
		} else if (doc.status === "Approved") {
			return [__("Approved"), "green", "status,=,Approved"];
		} else if (doc.status === "Sent to Supplier") {
			return [__("Sent to Supplier"), "green", "status,=,Sent to Supplier"];
		} else if (doc.status === "Confirmed") {
			return [__("Confirmed"), "blue", "status,=,Confirmed"];
		} else if (doc.status === "Pending Delivery") {
			return [__("Pending Delivery"), "yellow", "status,=,Pending Delivery"];
		} else if (doc.status === "Cancelled") {
			return [__("Cancelled"), "red", "status,=,Cancelled"];
		}
	},
};
