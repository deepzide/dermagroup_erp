import frappe
from frappe import _
from frappe.utils import getdate, today


def validate_purchase_receipt(doc, method):
	"""
	Validate Purchase Receipt on save/submit.
	"""
	# 1. Bill No is mandatory
	if not doc.bill_no:
		frappe.throw(_("Bill No (Factura) is mandatory for Receiving."))

	# 2. Uniqueness of Bill No per Supplier
	if doc.bill_no and doc.supplier:
		exists = frappe.db.exists(
			"Purchase Receipt", {"supplier": doc.supplier, "bill_no": doc.bill_no, "name": ["!=", doc.name]}
		)
		if exists:
			frappe.throw(_("Bill No {0} already exists for Supplier {1}").format(doc.bill_no, doc.supplier))

	# 3. Unsolicited Item Validation (Must have Purchase Order)
	for item in doc.items:
		# NOTE: User mentioned "Material Request" in parentheses, but "Orden de compra" usually maps to Purchase Order.
		# If the flow is MR -> PR directly, this field might need to be 'material_request'.
		# But strict "Recepcion de mercaderia" usually implies PO.
		has_purchase_order = True
		if not item.purchase_order:
			has_purchase_order = False

		has_open_material_request = True
		if not has_purchase_order:
			# Check if there is a submitted Material Request for this item and supplier
			has_open_material_request = frappe.db.sql(
				"""
				SELECT 1
				FROM `tabMaterial Request` mr
				JOIN `tabMaterial Request Item` mri ON mr.name = mri.parent
				WHERE mr.docstatus = 1
				AND mr.status != 'Cancelled'
				AND mr.suggested_supplier = %s
				AND mri.item_code = %s
				LIMIT 1
			""",
				(doc.supplier, item.item_code),
			)

		if not has_purchase_order and not has_open_material_request:
			frappe.throw(_(f"Row {item.idx}: {item.item_code} has not been requested"))

	# 4. Quantity Variance Validation (vs Material Request)
	for item in doc.items:
		if item.material_request_item:
			mr_item = frappe.db.get_value(
				"Material Request Item",
				item.material_request_item,
				["qty", "received_qty", "item_code"],
				as_dict=True,
			)
			if mr_item:
				# Compare vs Material Request Qty
				# Note: If multiple receipts are allowed, we should consider previous received_qty.
				# Assuming pending = mr_item.qty - mr_item.received_qty
				pending_qty = mr_item.qty - mr_item.received_qty

				if item.qty != pending_qty:
					diff = item.qty - pending_qty
					status = "Excess" if diff > 0 else "Shortage"
					msg = _(
						"Row {0}: Qty Variance for {1}. Requested/Pending: {2}, Received: {3}. ({4}: {5})"
					).format(item.idx, item.item_code, pending_qty, item.qty, status, abs(diff))
					frappe.msgprint(msg, title=_("Quantity Variance"), indicator="orange")

	# 5. Warehouse Override (Raw Material & Packaging -> Recepción - Pendiente de Control)
	# Automatically move these items to quarantine.
	target_warehouse = frappe.db.get_single_value("DermaGroup Stock Settings", "default_quarantine_warehouse")
	if not target_warehouse:
		# Fallback or Skip?
		# Let's fallback to hardcoded if not set, or skip functionality.
		# Ideally, we should skip if not configured to avoid errors.
		return

	for item in doc.items:
		if item.warehouse != target_warehouse:
			item.warehouse = target_warehouse
			frappe.msgprint(
				_("Row {0}: Item {1} automatically moved to QA pending warehouse '{2}'").format(
					item.idx, item.item_code, target_warehouse
				),
				alert=True,
			)


def validate_batch(doc, method):
	"""
	Validate Batch on save.
	"""
	# 1. Certificate Validation
	# If 'certificate_status' is 'Adjunto', verify we have an attachment?
	# Hard to verify attachment existence directly in validate without querying Files easily,
	# but we can rely on process or UI.
	# Here we enforce 'Pendiente de certificado' logic.

	if not doc.get("certificate_status"):
		doc.certificate_status = "Adjunto"  # Default

	if doc.certificate_status == "Adjunto":
		if not doc.certificate_attachment and not doc.certificate_reference_number:
			frappe.throw(
				_("Either Certificate Attachment or Reference Number is mandatory when status is 'Adjunto'")
			)

	if doc.certificate_status == "Pendiente de certificado":
		if not doc.missing_certificate_reason:
			frappe.throw(
				_("Missing Certificate Reason is mandatory when status is 'Pendiente de certificado'")
			)

		if not doc.missing_certificate_authorized_by:
			frappe.throw(_("Authorized By is mandatory when status is 'Pendiente de certificado'"))

	# 2. Expiry Date Validation
	if doc.expiry_date:
		if getdate(doc.expiry_date) <= getdate(today()):
			frappe.throw(_("Expiry Date must be greater than today."))


def notify_certificate_pending(doc, method):
	"""
	Notify Quality and General Management if certificate is pending.
	"""
	if doc.certificate_status == "Pendiente de certificado":
		# Check if status changed (to avoid spamming updates)
		# For new docs, get_doc_before_save() returns None.
		doc_before_save = doc.get_doc_before_save()
		old_status = doc_before_save.certificate_status if doc_before_save else None

		if old_status != "Pendiente de certificado":
			# Status changed to Pendiente, send notification
			# Roles synced with install.py source of truth
			roles = ["Quality Manager", "Director"]
			recipients = []
			for role in roles:
				users = frappe.get_all(
					"Has Role", filters={"role": role, "parenttype": "User"}, fields=["parent"]
				)
				recipients.extend([u.parent for u in users])

			if recipients:
				subject = _("Batch {0}: Pending Certificate").format(doc.name)
				message = _("""
					Batch {0} for Item {1} has been received with status 'Pendiente de certificado'.
					Reason: {2}
					Authorized By: {3}
					Please follow up.
				""").format(
					doc.name, doc.item, doc.missing_certificate_reason, doc.missing_certificate_authorized_by
				)

				frappe.sendmail(
					recipients=list(set(recipients)),  # Unique emails
					subject=subject,
					message=message,
					reference_doctype=doc.doctype,
					reference_name=doc.name,
				)


def validate_stock_entry(doc, method):
	"""
	Validate Stock Entry to prevent unauthorized consumption from Quarantine.
	Logic:
	- If Source Warehouse is Quarantine:
		- Allow if Target is Approved/Rejected (QA Move).
		- Allow if Batch Status is 'Pendiente de certificado' (Special Authorization).
		- Block otherwise.
	"""
	settings = frappe.get_single("DermaGroup Stock Settings")
	quarantine_wh = settings.default_quarantine_warehouse
	approved_wh = settings.default_approved_warehouse
	rejected_wh = settings.default_rejected_warehouse

	if not quarantine_wh:
		return

	for item in doc.items:
		if item.s_warehouse == quarantine_wh:
			# Check if it's a QA Move
			if item.t_warehouse and (item.t_warehouse == approved_wh or item.t_warehouse == rejected_wh):
				continue

			# Check Batch Status
			if item.batch_no:
				cert_status = frappe.db.get_value("Batch", item.batch_no, "certificate_status")
				if cert_status == "Pendiente de certificado":
					continue

			# If we are here, it's blocked
			frappe.throw(
				_(
					"Row {0}: Item {1} (Batch {2}) is in Quarantine ({3}). Consumption is blocked unless Batch key is 'Pendiente de certificado' or it is being moved to Approved/Rejected warehouses."
				).format(item.idx, item.item_code, item.batch_no, quarantine_wh)
			)
