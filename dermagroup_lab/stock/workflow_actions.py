import frappe
from frappe import _


def handle_pr_workflow_action(doc, method):
	"""
	Handle Purchase Receipt Workflow Actions:
	- If state changes to Approved: Move items from Quarantine to Approved Warehouse.
	- If state changes to Rejected: Move items from Quarantine to Rejected Warehouse.
	"""
	# Check if workflow_state changed
	if not doc.workflow_state:
		return

	# Get previous state (doc.get_doc_before_save might not work accurately for some workflow updates if they are done via db_set, but typically they are done via save)
	# For Workflow actions, typically it loads doc, sets state, and saves.
	old_doc = doc.get_doc_before_save()
	if not old_doc:
		return

	old_state = old_doc.workflow_state
	new_state = doc.workflow_state

	if old_state == new_state:
		return

	# Only proceed if DocStatus is Submitted (1)
	if doc.docstatus != 1:
		return

	if new_state == "Approved":
		create_stock_transfer(doc, "Approved")
	elif new_state == "Rejected":
		create_stock_transfer(doc, "Rejected")


def create_stock_transfer(doc, action_type):
	"""
	Create Stock Entry for Material Transfer.
	action_type: "Approved" or "Rejected"
	"""
	settings = frappe.get_single("DermaGroup Stock Settings")
	quarantine_wh = settings.default_quarantine_warehouse

	target_wh = None
	if action_type == "Approved":
		target_wh = settings.default_approved_warehouse
	elif action_type == "Rejected":
		target_wh = settings.default_rejected_warehouse

	if not quarantine_wh or not target_wh:
		frappe.msgprint(
			_("DermaGroup Stock Settings missing. Cannot auto-transfer stock for {0}.").format(action_type),
			alert=True,
		)
		return

	controlled_groups = ["Materia Prima", "Empaque", "Raw Material", "Packaging"]
	items_to_move = []

	for item in doc.items:
		# Check item group
		group = item.item_group
		if not group:
			group = frappe.db.get_value("Item", item.item_code, "item_group")

		is_controlled = group in controlled_groups

		# Check if item is in quarantine warehouse (it should be if our logic worked)
		# We use the item.warehouse from the PR row if it matches quarantine
		if is_controlled and item.warehouse == quarantine_wh:
			items_to_move.append(item)

	if not items_to_move:
		frappe.msgprint(_("No relevant items found in Quarantine Warehouse to move."), alert=True)
		return

	# Create Stock Entry
	stock_entry = frappe.new_doc("Stock Entry")
	stock_entry.stock_entry_type = "Material Transfer"
	stock_entry.purpose = "Material Transfer"
	stock_entry.set_stock_entry_type()  # Sets defaults

	# Override specific fields
	stock_entry.from_warehouse = quarantine_wh
	stock_entry.to_warehouse = target_wh
	stock_entry.purchase_receipt_no = doc.name  # Link for reference (custom field might be needed or remarks)
	stock_entry.remarks = f"Auto-transfer triggered by QA {action_type} for {doc.name}"

	for item in items_to_move:
		se_item = stock_entry.append("items", {})
		se_item.item_code = item.item_code
		se_item.qty = item.qty
		se_item.uom = item.uom
		se_item.conversion_factor = item.conversion_factor
		se_item.s_warehouse = quarantine_wh
		se_item.t_warehouse = target_wh
		se_item.batch_no = item.batch_no
		# Transfer cost? It should auto-fetch valuation rate.
		se_item.cost_center = item.cost_center

	try:
		stock_entry.insert()
		stock_entry.submit()
		frappe.msgprint(
			_("Stock Entry {0} created: {1} items moved to {2}").format(
				stock_entry.name, len(items_to_move), target_wh
			),
			alert=True,
		)
	except Exception as e:
		frappe.log_error(title="Failed to create Stock Entry for QA", message=str(e))
		frappe.msgprint(_("Failed to create automatic Stock Entry. Check Error Log."), indicator="red")
