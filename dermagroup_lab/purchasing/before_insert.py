import frappe
from frappe import _

from dermagroup_lab.purchasing.validations import check_duplicate_requests


def before_insert_material_request(doc, method=None):
	if doc.doctype != "Material Request":
		return
	if doc.get("material_request_type") != "Purchase":
		return

	item_codes = {row.get("item_code") for row in (doc.get("items") or []) if row.get("item_code")}
	supplier = doc.get("suggested_supplier")
	for item_code in item_codes:
		duplicates = check_duplicate_requests(item_code, supplier)
		if duplicates:
			frappe.msgprint(_("Similar orders found within 3 days"))
			return
