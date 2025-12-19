import frappe
from frappe import _


def send_material_request_to_supplier(material_request):
	"""
	Send material request to supplier via email with PDF attachment
	"""
	mr_doc = frappe.get_doc("Material Request", material_request)

	# Validate supplier email
	if not mr_doc.get("supplier_email"):
		frappe.throw(_("Supplier email is required"))

	# Get print format
	print_format = (
		frappe.db.get_value(
			"Property Setter", {"doc_type": "Material Request", "property": "default_print_format"}, "value"
		)
		or "Standard"
	)

	# Prepare email content
	subject = _("Material Request - {0}").format(mr_doc.name)

	message = frappe.render_template(
		"dermagroup_lab/templates/emails/material_request_to_supplier.html",
		{"doc": mr_doc, "supplier_name": mr_doc.get("suggested_supplier")},
	)

	if not message:
		return

	# Send email
	frappe.sendmail(
		recipients=[mr_doc.get("supplier_email")],
		subject=subject,
		message=message,
		reference_doctype="Material Request",
		reference_name=mr_doc.name,
		attachments=[frappe.attach_print("Material Request", mr_doc.name, print_format=print_format)],
	)

	return True


def notify_purchasing_of_material_request(mr_doc):
	if mr_doc.doctype != "Material Request":
		return

	if mr_doc.get("material_request_type") != "Purchase":
		return

	users = frappe.get_all(
		"Has Role",
		filters={"role": "Purchasing Manager", "parenttype": "User"},
		fields=["parent"],
	)
	user_names = [u.parent for u in users if u.parent not in ["Administrator", "Guest"]]
	if not user_names:
		return

	emails = frappe.get_all(
		"User",
		filters={"name": ["in", user_names], "enabled": 1},
		fields=["email"],
	)
	recipients = list({e.email for e in emails if e.email})
	if not recipients:
		return

	subject = _("Material Request - {0}").format(mr_doc.name)
	message = _("A new Material Request is ready for review: {0}").format(mr_doc.name)

	try:
		frappe.sendmail(
			recipients=recipients,
			subject=subject,
			message=message,
			reference_doctype="Material Request",
			reference_name=mr_doc.name,
		)
	except Exception:
		frappe.log_error("Unable to notify Purchasing Manager")
		return
