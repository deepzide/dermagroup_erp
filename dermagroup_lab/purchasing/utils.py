import frappe
from frappe import _
from frappe.utils import add_days, flt, nowdate

from dermagroup_lab.purchasing.notifications import notify_purchasing_of_material_request
from dermagroup_lab.purchasing.validations import check_duplicate_requests


@frappe.whitelist()
def get_last_purchase_details(item_code, warehouse=None):
	"""
	Get details from the last purchase order for an item
	Returns: dict with purchase_order, supplier, posting_date, qty, rate
	"""
	filters = {"item_code": item_code, "docstatus": 1}

	if warehouse:
		filters["warehouse"] = warehouse

	# Get the most recent purchase receipt item
	last_purchase = frappe.db.get_all(
		"Purchase Receipt Item",
		filters=filters,
		fields=["parent", "qty", "rate", "creation"],
		order_by="creation desc",
		limit=1,
	)

	if not last_purchase:
		# Try Purchase Order if no receipt found
		last_purchase = frappe.db.get_all(
			"Purchase Order Item",
			filters=filters,
			fields=["parent", "qty", "rate", "schedule_date as posting_date"],
			order_by="schedule_date desc",
			limit=1,
		)

	if last_purchase:
		purchase_doc = last_purchase[0]

		# Get supplier from parent document
		parent_doctype = (
			"Purchase Receipt"
			if frappe.db.exists("Purchase Receipt", purchase_doc.get("parent"))
			else "Purchase Order"
		)
		supplier = frappe.db.get_value(parent_doctype, purchase_doc.get("parent"), "supplier")

		return {
			"purchase_order": purchase_doc.get("parent"),
			"supplier": supplier,
			"qty": purchase_doc.get("qty"),
			"rate": purchase_doc.get("rate"),
		}

	return {}


@frappe.whitelist()
def get_stock_projection(item_code, warehouse):
	"""
	Calculate projected stock: Current + In Transit - Reserved
	Returns: dict with actual_qty, ordered_qty, reserved_qty, projected_qty, reorder_level
	"""
	# Get current stock from Bin
	bin_data = (
		frappe.db.get_value(
			"Bin",
			{"item_code": item_code, "warehouse": warehouse},
			["actual_qty", "ordered_qty", "reserved_qty", "projected_qty"],
			as_dict=True,
		)
		or {}
	)

	# Get reorder level from Item Reorder
	reorder_level = (
		frappe.db.get_value(
			"Item Reorder", {"parent": item_code, "warehouse": warehouse}, "warehouse_reorder_level"
		)
		or 0
	)

	return {
		"actual_qty": flt(bin_data.get("actual_qty", 0)),
		"ordered_qty": flt(bin_data.get("ordered_qty", 0)),
		"reserved_qty": flt(bin_data.get("reserved_qty", 0)),
		"projected_qty": flt(bin_data.get("projected_qty", 0)),
		"reorder_level": flt(reorder_level),
	}


@frappe.whitelist()
def validate_stock_before_production(doc, method):
	"""
	Hook for Work Order - validate stock before creating production order
	If stock is insufficient, create Material Request automatically
	"""
	if doc.doctype != "Work Order":
		return

	# Get required items from BOM
	bom_items = frappe.db.sql(
		"""
		SELECT
			item_code,
			qty,
			stock_uom,
			source_warehouse
		FROM
			`tabBOM Item`
		WHERE
			parent = %(bom)s
	""",
		{"bom": doc.bom_no},
		as_dict=True,
	)

	insufficient_items = []

	for item in bom_items:
		# Calculate required qty based on production qty
		required_qty = flt(item.qty) * flt(doc.qty)

		# Get stock projection
		warehouse = item.source_warehouse or doc.source_warehouse
		if not warehouse:
			continue

		stock_data = get_stock_projection(item.item_code, warehouse)

		if stock_data.get("projected_qty", 0) < required_qty:
			insufficient_items.append(
				{
					"item_code": item.item_code,
					"required_qty": required_qty,
					"available_qty": stock_data.get("projected_qty", 0),
					"shortage": required_qty - stock_data.get("projected_qty", 0),
					"warehouse": warehouse,
				}
			)

	# If there are insufficient items, create material requests
	if insufficient_items:
		create_auto_material_requests(insufficient_items, doc)

		# Show message to user
		msg = _("Material Requests created for insufficient stock items:")
		for item in insufficient_items:
			msg += f"<br>• {item['item_code']}: Shortage of {item['shortage']} {item.get('stock_uom', '')}"

		frappe.msgprint(msg, title=_("Stock Shortage"), indicator="orange")


def create_auto_material_requests(items, work_order_doc):
	"""
	Create material requests for items with insufficient stock
	"""
	for item_data in items:
		# Check if similar request exists in last 3 days
		duplicates = check_duplicate_requests(item_data["item_code"], days=3)

		if duplicates:
			frappe.msgprint(
				_("Skipped {0} because a similar Material Request exists in the last {1} days").format(
					frappe.bold(item_data["item_code"]), 3
				)
			)
			continue

		# Create new Material Request
		mr = frappe.new_doc("Material Request")
		mr.material_request_type = "Purchase"
		mr.company = work_order_doc.company
		mr.transaction_date = nowdate()
		mr.schedule_date = add_days(nowdate(), 7)  # Default 7 days lead time
		mr.auto_created_via_reorder = 1

		# Add item
		mr.append(
			"items",
			{
				"item_code": item_data["item_code"],
				"qty": item_data["shortage"],
				"warehouse": item_data["warehouse"],
				"schedule_date": add_days(nowdate(), 7),
			},
		)

		# Save and submit
		mr.flags.ignore_mandatory = True
		mr.insert()
		mr.submit()
		notify_purchasing_of_material_request(mr)

		frappe.msgprint(
			_("Material Request {0} created for {1}").format(frappe.bold(mr.name), item_data["item_code"])
		)
