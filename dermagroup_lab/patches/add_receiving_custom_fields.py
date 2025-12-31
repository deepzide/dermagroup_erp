from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	print("Adding custom fields to Purchase Receipt and Batch")
	# Purchase Receipt Fields
	create_custom_field(
		"Purchase Receipt",
		{
			"fieldname": "purchase_type",
			"label": "Purchase Type",
			"fieldtype": "Select",
			"options": "\nLocal\nImportación",
			"default": "Local",
			"insert_after": "supplier",
		},
	)

	create_custom_field(
		"Purchase Receipt",
		{
			"fieldname": "bill_no",
			"label": "Bill No (Factura)",
			"fieldtype": "Data",
			"insert_after": "supplier_delivery_note",
		},
	)

	create_custom_field(
		"Purchase Receipt",
		{"fieldname": "bill_date", "label": "Bill Date", "fieldtype": "Date", "insert_after": "bill_no"},
	)

	# Batch Fields
	create_custom_field(
		"Batch",
		{
			"fieldname": "certificate_status",
			"label": "Certificate Status",
			"fieldtype": "Select",
			"options": "Adjunto\nPendiente de certificado",
			"default": "Adjunto",
			"insert_after": "expiry_date",
		},
	)

	create_custom_field(
		"Batch",
		{
			"fieldname": "certificate_attachment",
			"label": "Certificate Attachment",
			"fieldtype": "Attach",
			"insert_after": "certificate_status",
			"depends_on": "eval:doc.certificate_status == 'Adjunto'",
		},
	)

	create_custom_field(
		"Batch",
		{
			"fieldname": "certificate_reference_number",
			"label": "Certificate Reference Number",
			"fieldtype": "Data",
			"insert_after": "certificate_attachment",
			"depends_on": "eval:doc.certificate_status == 'Adjunto'",
		},
	)

	create_custom_field(
		"Batch",
		{
			"fieldname": "missing_certificate_reason",
			"label": "Missing Certificate Reason",
			"fieldtype": "Small Text",
			"insert_after": "certificate_status",
			"depends_on": "eval:doc.certificate_status == 'Pendiente de certificado'",
			"mandatory_depends_on": "eval:doc.certificate_status == 'Pendiente de certificado'",
		},
	)

	create_custom_field(
		"Batch",
		{
			"fieldname": "missing_certificate_authorized_by",
			"label": "Authorized By",
			"fieldtype": "Link",
			"options": "User",
			"insert_after": "missing_certificate_reason",
			"depends_on": "eval:doc.certificate_status == 'Pendiente de certificado'",
			"mandatory_depends_on": "eval:doc.certificate_status == 'Pendiente de certificado'",
		},
	)
