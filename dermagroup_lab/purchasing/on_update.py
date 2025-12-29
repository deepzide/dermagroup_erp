import frappe
from frappe import _

from dermagroup_lab.purchasing.enums import ApprovalStatus
from dermagroup_lab.purchasing.notifications import (
	notify_purchasing_of_material_request,
	send_material_request_to_supplier,
)


def on_update_material_request(doc, method=None):
	if doc.doctype != "Material Request":
		return
	if doc.get("material_request_type") != "Purchase":
		return

	match doc.status:
		case ApprovalStatus.PENDING_APPROVAL.value:
			notify_purchasing_of_material_request(doc)
		case ApprovalStatus.SENT_TO_SUPPLIER.value:
			if not doc.get("supplier_email"):
				frappe.throw(_("Supplier email is required"))
			else:
				send_material_request_to_supplier(doc)
		case _:
			pass
