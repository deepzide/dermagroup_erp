import frappe

from dermagroup_lab.purchasing.enums import ApprovalStatus


def execute():
	"""Customize Material Request status field options and make it editable after submit"""

	# Update status field options
	if frappe.db.exists(
		"Property Setter", {"doc_type": "Material Request", "field_name": "status", "property": "options"}
	):
		property_setter = frappe.get_doc(
			"Property Setter", {"doc_type": "Material Request", "field_name": "status", "property": "options"}
		)
	else:
		property_setter = frappe.new_doc("Property Setter")
		property_setter.doc_type = "Material Request"
		property_setter.doctype_or_field = "DocField"
		property_setter.field_name = "status"
		property_setter.property = "options"
		property_setter.property_type = "Text"

	property_setter.value = "\n".join(status.value for status in ApprovalStatus)
	property_setter.save()

	# Make status field editable after submit
	if frappe.db.exists(
		"Property Setter",
		{"doc_type": "Material Request", "field_name": "status", "property": "allow_on_submit"},
	):
		allow_submit_setter = frappe.get_doc(
			"Property Setter",
			{"doc_type": "Material Request", "field_name": "status", "property": "allow_on_submit"},
		)
	else:
		allow_submit_setter = frappe.new_doc("Property Setter")
		allow_submit_setter.doc_type = "Material Request"
		allow_submit_setter.doctype_or_field = "DocField"
		allow_submit_setter.field_name = "status"
		allow_submit_setter.property = "allow_on_submit"
		allow_submit_setter.property_type = "Check"

	allow_submit_setter.value = "1"
	allow_submit_setter.save()

	# Set default value for status field
	if frappe.db.exists(
		"Property Setter", {"doc_type": "Material Request", "field_name": "status", "property": "default"}
	):
		default_setter = frappe.get_doc(
			"Property Setter", {"doc_type": "Material Request", "field_name": "status", "property": "default"}
		)
	else:
		default_setter = frappe.new_doc("Property Setter")
		default_setter.doc_type = "Material Request"
		default_setter.doctype_or_field = "DocField"
		default_setter.field_name = "status"
		default_setter.property = "default"
		default_setter.property_type = "Text"

	default_setter.value = ApprovalStatus.PENDING_APPROVAL.value
	default_setter.save()

	frappe.db.commit()
	frappe.clear_cache(doctype="Material Request")

	# Update existing draft Material Requests without status
	frappe.db.sql(
		"""
        UPDATE `tabMaterial Request`
        SET status = %s
        WHERE docstatus = 0
        AND (status IS NULL OR status = '' OR status = 'Draft')
    """,
		(ApprovalStatus.PENDING_APPROVAL.value,),
	)

	frappe.db.commit()
