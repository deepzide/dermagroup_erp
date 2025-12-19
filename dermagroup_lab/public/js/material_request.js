frappe.ui.form.on("Material Request", {
	refresh: function (frm) {
		const min_estimated_arrival_date = frappe.datetime.add_days(
			frappe.datetime.get_today(),
			1
		);
		const min_date_obj = frappe.datetime.str_to_obj(min_estimated_arrival_date);
		cur_frm.fields_dict.estimated_arrival_date.datepicker.update({
			minDate: min_date_obj,
		});

		const status_colors = {
			"Pending Approval": "blue",
			"Under Review": "purple",
			Approved: "green",
			"Sent to Supplier": "green",
			Confirmed: "darkgreen",
			"Pending Delivery": "yellow",
			Cancelled: "red",
		};

		if (frm.doc.custom_approval_status) {
			frm.page.set_indicator(
				frm.doc.custom_approval_status,
				status_colors[frm.doc.custom_approval_status]
			);
		}

		// Botones para documentos submitted
		if (frm.doc.docstatus === 1) {
			if (frm.doc.custom_approval_status === "Sent to Supplier") {
				frm.add_custom_button(
					__("Confirm Receipt"),
					function () {
						frappe.call({
							method: "frappe.client.set_value",
							args: {
								doctype: "Material Request",
								name: frm.doc.name,
								fieldname: "custom_approval_status",
								value: "Confirmed",
							},
							callback: function (r) {
								frm.reload_doc();
							},
						});
					},
					__("Actions")
				);

				frm.add_custom_button(
					__("Mark Pending Delivery"),
					function () {
						frappe.call({
							method: "frappe.client.set_value",
							args: {
								doctype: "Material Request",
								name: frm.doc.name,
								fieldname: "custom_approval_status",
								value: "Pending Delivery",
							},
							callback: function (r) {
								frm.reload_doc();
							},
						});
					},
					__("Actions")
				);
			}
		}
		// Botones para documentos draft (docstatus = 0)
		else if (frm.doc.docstatus === 0) {
			if (!frm.doc.custom_approval_status || frm.doc.custom_approval_status === "Draft") {
				frm.add_custom_button(__("Submit for Approval"), function () {
					frm.set_value("custom_approval_status", "Pending Approval");
					frm.save();
				});
			}

			if (frm.doc.custom_approval_status === "Pending Approval") {
				frm.add_custom_button(__("Start Review"), function () {
					frm.set_value("custom_approval_status", "Under Review");
					frm.save();
				});
			}

			if (frm.doc.custom_approval_status === "Under Review") {
				frm.add_custom_button(
					__("Approve"),
					function () {
						frm.set_value("custom_approval_status", "Approved");
						frm.save();
					},
					__("Actions")
				);
			}

			if (frm.doc.custom_approval_status === "Approved") {
				frm.add_custom_button(__("Send to Supplier"), function () {
					frappe.call({
						method: "frappe.client.set_value",
						args: {
							doctype: "Material Request",
							name: frm.doc.name,
							fieldname: "custom_approval_status",
							value: "Sent to Supplier",
						},
						callback: function (r) {
							frm.reload_doc();
						},
					});
				});
			}
		}
	},

	estimated_arrival_date: function (frm) {
		const min_estimated_arrival_date = frappe.datetime.add_days(
			frappe.datetime.get_today(),
			1
		);
		if (
			frm.doc.estimated_arrival_date &&
			frappe.datetime.compare_date(
				frm.doc.estimated_arrival_date,
				min_estimated_arrival_date
			) < 0
		) {
			frappe.msgprint(__("Estimated Arrival Date must be in the future."));
			frm.set_value("estimated_arrival_date", null);
		}
	},
});

function dermagroup_get_mri_fieldname_by_label(label) {
	const meta = frappe.get_meta("Material Request Item");
	const fields = (meta && meta.fields) || [];
	const df = fields.find((f) => (f.label || "").trim() === label);
	return df ? df.fieldname : null;
}

function dermagroup_autofill_last_purchase(frm, cdt, cdn) {
	if (!frm || !frm.doc || frm.doc.material_request_type !== "Purchase") {
		return;
	}

	const row = locals[cdt] && locals[cdt][cdn];
	if (!row || !row.item_code) {
		return;
	}

	frappe.call({
		method: "dermagroup_lab.purchasing.utils.get_last_purchase_details",
		args: {
			item_code: row.item_code,
			warehouse: row.warehouse,
		},
		callback: function (r) {
			const currentRow = locals[cdt] && locals[cdt][cdn];
			if (!currentRow || !currentRow.item_code || currentRow.item_code !== row.item_code) {
				return;
			}

			const data = (r && r.message) || {};
			if (!data || (data.qty == null && data.rate == null)) {
				return;
			}

			if (data.qty != null) {
				frappe.model.set_value(cdt, cdn, "qty", data.qty);
			}
			if (data.rate != null) {
				frappe.model.set_value(cdt, cdn, "rate", data.rate);
			}
		},
	});
}

frappe.ui.form.on("Material Request Item", {
	item_code: function (frm, cdt, cdn) {
		dermagroup_autofill_last_purchase(frm, cdt, cdn);
	},
	warehouse: function (frm, cdt, cdn) {
		dermagroup_autofill_last_purchase(frm, cdt, cdn);
	},
});
