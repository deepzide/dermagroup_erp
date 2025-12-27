/**
 * Handles Material Request form customizations
 */

// Status configuration - usando los valores del Enum de Python
const STATUS_CONFIG = {
	"Pending Approval": "blue",
	"Under Review": "orange",
	Approved: "green",
	"Sent to Supplier": "green",
	Confirmed: "blue",
	"Pending Delivery": "yellow",
	Cancelled: "red",
};

// Validation rules
frappe.ui.form.on("Material Request", {
	/**
	 * Prevent submission if not approved
	 */
	on_submit: function (form) {
		if (!["Approved"].includes(form.doc.status)) {
			frappe.msgprint(__("Please approve this request before submitting"));
			frappe.validated = false;
		}
	},

	/**
	 * Main refresh handler
	 */
	refresh: function (form) {
		const { doc } = form;

		// Setup primary action based on approval status
		setupPrimaryAction(form);

		// Setup date picker constraints
		setupDatePickerConstraints(form);

		// Set status indicator
		if (doc.status) {
			form.page.set_indicator(__(doc.status), STATUS_CONFIG[doc.status] || "gray");
		}

		// Get user roles
		const userRoles = frappe.user_roles || [];
		const hasProductionAccess = userRoles.includes("Production Manager");
		const hasPurchasingAccess = userRoles.includes("Purchasing Manager");

		// Handle document state-specific actions
		if (doc.docstatus === 1) {
			handleSubmittedDocument(form, doc, hasPurchasingAccess);
		} else if (doc.docstatus === 0) {
			handleDraftDocument(form, doc, hasProductionAccess, hasPurchasingAccess);
		}

		// Auto-fill supplier for new purchase requests
		if (doc.__islocal && doc.material_request_type === "Purchase") {
			autoFillSupplierFromLastPurchase(form);
		}
	},

	/**
	 * Validates estimated arrival date
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
 * Setup primary action button based on approval status
 */
function setupPrimaryAction(form) {
	if (form.doc.docstatus !== 0) return;

	const isApproved = ["Approved"].includes(form.doc.status);

	// Remove default Submit button
	form.page.clear_primary_action();

	if (isApproved) {
		form.page.set_primary_action(__("Submit"), function () {
			form.save("Submit");
		});
	} else {
		form.page.set_primary_action(__("Save"), function () {
			form.save();
		});
	}
}

/**
 * Setup date picker constraints for estimated arrival date
 */
function setupDatePickerConstraints(form) {
	const today = frappe.datetime.get_today();
	const minArrivalDate = frappe.datetime.add_days(today, 1);
	const minDateObj = frappe.datetime.str_to_obj(minArrivalDate);

	form.fields_dict.estimated_arrival_date?.datepicker?.update({
		minDate: minDateObj,
	});
}

/**
 * Handles actions for submitted documents
 */
function handleSubmittedDocument(form, doc, hasPurchasingAccess) {
	if (!hasPurchasingAccess) return;

	const { status } = doc;

	switch (status) {
		case "Approved":
			addActionButton(form, "Send to Supplier", () =>
				updateStatus(form, "Sent to Supplier")
			);
			break;

		case "Sent to Supplier":
			addActionButton(form, "Confirm Receipt", () => updateStatus(form, "Confirmed"));
			addActionButton(form, "Mark Pending Delivery", () =>
				updateStatus(form, "Pending Delivery")
			);
			break;

		case "Pending Delivery":
			addActionButton(form, "Confirm Receipt", () => updateStatus(form, "Confirmed"));
			break;
	}
}

/**
 * Handles actions for draft documents
 */
function handleDraftDocument(form, doc, hasProductionAccess, hasPurchasingAccess) {
	const { status } = doc;

	if (hasPurchasingAccess) {
		if (status === "Pending Approval") {
			addActionButton(form, "Approve", () => updateStatus(form, "Approved", true));
		}
	}
}

/**
 * Updates document status
 */
function updateStatus(form, status, shouldSave = false) {
	if (shouldSave) {
		form.set_value("status", status);
		form.save();
	} else {
		frappe.call({
			method: "frappe.client.set_value",
			args: {
				doctype: "Material Request",
				name: form.doc.name,
				fieldname: "status",
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
