import frappe


def execute():
	frappe.reload_doc("workflow", "doctype", "workflow_state")
	frappe.reload_doc("workflow", "doctype", "workflow_action_master")
	frappe.reload_doc("workflow", "doctype", "workflow")

	# 1. Create Workflow States
	states = ["Draft", "Received Pending QA", "Approved", "Rejected"]

	colors = {"Draft": "Primary", "Received Pending QA": "Info", "Approved": "Success", "Rejected": "Danger"}

	for state in states:
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{
					"doctype": "Workflow State",
					"workflow_state_name": state,
					"style": colors.get(state, "Primary"),
				}
			).insert(ignore_permissions=True)

	# 1.5 Create Workflow Actions
	actions = ["Submit", "Approve", "Reject"]
	for action in actions:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
				ignore_permissions=True
			)

	# 2. Create Workflow
	workflow_name = "Purchase Receipt QA Workflow"

	if not frappe.db.exists("Workflow", workflow_name):
		doc = frappe.new_doc("Workflow")
		doc.workflow_name = workflow_name
		doc.document_type = "Purchase Receipt"
		doc.is_active = 1
		doc.override_status = 1
		doc.workflow_state_field = "workflow_state"

		# States
		states_data = [
			{
				"state": "Draft",
				"doc_status": 0,
				"allow_edit": "Reception Manager",
				"update_field": None,
				"update_value": None,
				"is_optional_state": 0,
			},
			{
				"state": "Received Pending QA",
				"doc_status": 1,
				"allow_edit": "Quality Manager",
				"update_field": None,
				"update_value": None,
				"is_optional_state": 0,
			},
			{
				"state": "Approved",
				"doc_status": 1,
				"allow_edit": "Quality Manager",
				"update_field": None,
				"update_value": None,
				"is_optional_state": 0,
			},
			{
				"state": "Rejected",
				"doc_status": 1,
				"allow_edit": "Quality Manager",
				"update_field": None,
				"update_value": None,
				"is_optional_state": 0,
			},
		]
		for s in states_data:
			doc.append("states", s)

		# Transitions
		transitions_data = [
			{
				"state": "Draft",
				"action": "Submit",
				"next_state": "Received Pending QA",
				"allowed": "Reception Manager",
			},
			{
				# Backup for Purchasing
				"state": "Draft",
				"action": "Submit",
				"next_state": "Received Pending QA",
				"allowed": "Purchasing Manager",
			},
			{
				"state": "Received Pending QA",
				"action": "Approve",
				"next_state": "Approved",
				"allowed": "Quality Manager",
			},
			{
				"state": "Received Pending QA",
				"action": "Reject",
				"next_state": "Rejected",
				"allowed": "Quality Manager",
			},
		]
		for t in transitions_data:
			doc.append("transitions", t)

		doc.insert()
		print("Created Workflow: " + workflow_name)
	else:
		print("Workflow already exists: " + workflow_name)
