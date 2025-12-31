from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	create_custom_field(
		"Item Group",
		{
			"fieldname": "batch_prefix",
			"label": "Batch Prefix",
			"fieldtype": "Data",
			"length": 5,
			"insert_after": "item_group_name",
			"description": "Prefix for Batch ID generation (e.g. MP, ENV)",
		},
	)
