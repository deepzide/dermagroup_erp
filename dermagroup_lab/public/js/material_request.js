/**
 * Handles Material Request form customizations
 */
// Add custom validation to prevent submission if not approved
frappe.ui.form.on("Material Request", {
	on_submit: function (form) {
		// Only allow submission if status is 'Approved'
		if (!["Approved"].includes(form.doc.custom_approval_status)) {
			frappe.msgprint(__("Please approve this request before submitting"));
			frappe.validated = false;
		}
	},
	/**
	 * Refresh handler for Material Request form
	 * @param {Object} form - The form object
	 */
	refresh: function (form) {
		const { doc } = form;

		// Disable submit button if not approved
		if (form.doc.docstatus === 0) {
			// Only for draft documents
			const is_approved = ["Approved"].includes(form.doc.custom_approval_status);

			// Remove the default Submit button
			form.page.clear_primary_action();

			if (is_approved) {
				// If approved, show Submit button
				form.page.set_primary_action(__("Submit"), function () {
					form.save("Submit");
				});
			} else {
				// If not approved, show only Save button
				form.page.set_primary_action(__("Save"), function () {
					form.save();
				});
			}
		}
		const today = frappe.datetime.get_today();
		const minArrivalDate = frappe.datetime.add_days(today, 1);
		const minDateObj = frappe.datetime.str_to_obj(minArrivalDate);

		// Update date picker constraints
		form.fields_dict.estimated_arrival_date?.datepicker?.update({
			minDate: minDateObj,
		});

		// Status color mapping
		const statusColors = {
			"Pending Approval": "blue",
			Approved: "green",
			"Sent to Supplier": "green",
			Confirmed: "blue",
			"Pending Delivery": "yellow",
			Cancelled: "red",
		};

		// Set status indicator if status exists
		if (doc.custom_approval_status) {
			form.page.set_indicator(
				__(doc.custom_approval_status),
				statusColors[doc.custom_approval_status]
			);
		}

		// Get user roles
		const userRoles = frappe.user_roles || [];
		const hasProductionAccess = userRoles.includes("Production Manager");
		const hasPurchasingAccess = userRoles.includes("Purchasing Manager");

		// Handle submitted documents
		if (doc.docstatus === 1) {
			handleSubmittedDocument(form, doc, hasPurchasingAccess);
		}
		// Handle draft documents
		else if (doc.docstatus === 0) {
			handleDraftDocument(form, doc, hasProductionAccess, hasPurchasingAccess);
		}

		// Auto-fill supplier from last purchase if new document
		if (doc.__islocal && doc.material_request_type === "Purchase") {
			autoFillSupplierFromLastPurchase(form);
		}
	},

	/**
	 * Validates estimated arrival date
	 * @param {Object} form - The form object
	 */
	estimated_arrival_date: function (form) {
		const { doc } = form;
		const minDate = frappe.datetime.add_days(frappe.datetime.get_today(), 1);

		if (
			doc.estimated_arrival_date &&
			frappe.datetime.compare_date(doc.estimated_arrival_date, minDate) < 0
		) {
			frappe.msgprint(__("Estimated Arrival Date must be in the future."));
			form.set_value("estimated_arrival_date", null);
		}
	},
});

/**
 * Handles actions for submitted documents
 */
function handleSubmittedDocument(form, doc, hasPurchasingAccess) {
	if (doc.custom_approval_status === "Sent to Supplier" && hasPurchasingAccess) {
		addActionButton(form, "Confirm Receipt", () => updateStatus(form, "Confirmed"));

		addActionButton(form, "Mark Pending Delivery", () =>
			updateStatus(form, "Pending Delivery")
		);
	}
	// Purchasing manager actions
	if (hasPurchasingAccess) {
		if (doc.custom_approval_status === "Approved") {
			addActionButton(form, "Send to Supplier", () =>
				updateStatus(form, "Sent to Supplier")
			);
		}

		if (doc.custom_approval_status === "Pending Delivery") {
			addActionButton(form, "Confirm Receipt", () => updateStatus(form, "Confirmed"));
		}
	}
}

/**
 * Handles actions for draft documents
 */
function handleDraftDocument(form, doc, hasProductionAccess, hasPurchasingAccess) {
	const { custom_approval_status: status } = doc;

	// Production manager actions
	if (hasProductionAccess) {
		if (!status || status === "Draft") {
			addActionButton(form, "Submit for Approval", () =>
				updateStatus(form, "Pending Approval", true)
			);
		}
	}

	if (hasPurchasingAccess) {
		if (doc.custom_approval_status === "Pending Approval") {
			addActionButton(form, "Approve", () => updateStatus(form, "Approved", true));
		}
	}
}

/**
 * Updates document status
 */
function updateStatus(form, status, shouldSave = false) {
	if (shouldSave) {
		form.set_value("custom_approval_status", status);
		form.save();
	} else {
		frappe.call({
			method: "frappe.client.set_value",
			args: {
				doctype: "Material Request",
				name: form.doc.name,
				fieldname: "custom_approval_status",
				value: status,
			},
			callback: () => form.reload_doc(),
		});
	}
}

/**
 * Adds an action button to the form
 */
function addActionButton(form, label, onClick, group = "Actions") {
	form.add_custom_button(__(label), onClick, __(group));
}

/**
 * Gets field name by label from Meta
 */
function getFieldNameByLabel(doctype, label) {
	const meta = frappe.get_meta(doctype);
	const fields = meta?.fields || [];
	const field = fields.find((f) => (f.label || "").trim() === label);
	return field?.fieldname;
}

/**
 * Autofills purchase details for an item
 */
function autofillLastPurchase(form, row, rowName) {
	if (!form?.doc || form.doc.material_request_type !== "Purchase") return;

	const rowData = locals[row]?.[rowName];
	if (!rowData?.item_code) return;

	frappe.call({
		method: "dermagroup_lab.purchasing.utils.get_last_purchase_details",
		args: {
			item_code: rowData.item_code,
			warehouse: rowData.warehouse,
		},
		callback: (response) => {
			const currentRow = locals[row]?.[rowName];
			if (!currentRow?.item_code || currentRow.item_code !== rowData.item_code) return;

			const { message: data = {} } = response || {};
			if (data.qty == null && data.rate == null) return;

			if (data.qty != null) {
				frappe.model.set_value(row, rowName, "qty", data.qty);
			}
			if (data.rate != null) {
				frappe.model.set_value(row, rowName, "rate", data.rate);
			}
		},
	});
}

// Item table events
frappe.ui.form.on("Material Request Item", {
	item_code: (form, cdt, cdn) => autofillLastPurchase(form, cdt, cdn),
	warehouse: (form, cdt, cdn) => autofillLastPurchase(form, cdt, cdn),
});

/**
 * Auto-fills supplier from last purchase order
 */
function autoFillSupplierFromLastPurchase(form) {
	const { doc } = form;

	// Only proceed if there are items and no supplier is set
	if (!doc.items?.length || doc.supplier) return;
	// Get all unique item codes
	const itemCodes = [...new Set(doc.items.map((item) => item.item_code))];

	// Get the first item's last purchase details
	frappe.call({
		method: "dermagroup_lab.purchasing.utils.get_last_purchase_details",
		args: {
			item_code: itemCodes[0],
			warehouse: doc.warehouse,
		},
		callback: (response) => {
			const data = response.message || {};
			if (data.supplier) {
				form.set_value("suggested_supplier", data.supplier);
			}
		},
	});
}
