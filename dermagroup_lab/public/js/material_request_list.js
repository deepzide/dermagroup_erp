const STATUS_CONFIG = {
	"Pending Approval": "blue",
	"Under Review": "orange",
	Approved: "green",
	"Sent to Supplier": "green",
	Confirmed: "blue",
	"Pending Delivery": "yellow",
	Cancelled: "red",
};

frappe.listview_settings["Material Request"] = {
	has_indicator_for_draft: true,
	has_indicator_for_cancelled: true,
	get_indicator: function (doc) {
		const color = STATUS_CONFIG[doc.status];
		if (color) {
			return [__(doc.status), color, `status,=,${doc.status}`];
		} else {
			return [__(doc.status), "grey", `status,=,${doc.status}`];
		}
	},
};
