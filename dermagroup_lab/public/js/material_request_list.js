frappe.listview_settings["Material Request"] = {
	add_fields: ["custom_approval_status"],

	get_indicator: function (doc) {
		const statusColors = {
			"Pending Approval": "blue",
			Approved: "green",
			"Sent to Supplier": "green",
			Confirmed: "blue",
			"Pending Delivery": "yellow",
			Cancelled: "red",
		};

		if (doc.custom_approval_status) {
			return [
				__(doc.custom_approval_status),
				statusColors[doc.custom_approval_status] || "gray",
				`custom_approval_status,=,${doc.custom_approval_status}`,
			];
		}
	},

	// Opcional: Formatear la columna con pills coloridos
	formatters: {
		custom_approval_status(value) {
			const statusColors = {
				"Pending Approval": "blue",
				Approved: "green",
				"Sent to Supplier": "green",
				Confirmed: "blue",
				"Pending Delivery": "yellow",
				Cancelled: "red",
			};

			if (value && statusColors[value]) {
				return `<span class="indicator-pill ${statusColors[value]}">${__(value)}</span>`;
			}
			return value || "";
		},
	},
};
