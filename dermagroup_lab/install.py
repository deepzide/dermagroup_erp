# Copyright (c) 2024, DeepZide and contributors
# For license information, please see license.txt

import frappe
from frappe.permissions import add_permission, update_permission_property


def after_install():
	"""
	Configure custom permissions for Material Request after app installation
	"""
	ensure_roles_exist()
	setup_material_request_permissions()


def ensure_roles_exist():
	roles = ["Production Manager", "Purchasing Manager", "Director"]
	for role_name in roles:
		if frappe.db.exists("Role", role_name):
			continue

		frappe.get_doc(
			{
				"doctype": "Role",
				"role_name": role_name,
				"desk_access": 1,
				"disabled": 0,
				"is_custom": 1,
			}
		).insert(ignore_permissions=True)


def setup_material_request_permissions():
	"""
	Set up role-based permissions for Material Request
	"""
	# Production Manager permissions
	add_permission("Material Request", "Production Manager", 0)
	update_permission_property("Material Request", "Production Manager", 0, "read", 1)
	update_permission_property("Material Request", "Production Manager", 0, "write", 1)
	update_permission_property("Material Request", "Production Manager", 0, "create", 1)
	update_permission_property("Material Request", "Production Manager", 0, "submit", 1)
	update_permission_property("Material Request", "Production Manager", 0, "report", 1)
	update_permission_property("Material Request", "Production Manager", 0, "export", 1)
	update_permission_property("Material Request", "Production Manager", 0, "print", 1)
	update_permission_property("Material Request", "Production Manager", 0, "email", 1)
	update_permission_property("Material Request", "Production Manager", 0, "share", 1)

	# Purchasing Manager permissions (full access)
	add_permission("Material Request", "Purchasing Manager", 0)
	update_permission_property("Material Request", "Purchasing Manager", 0, "read", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "write", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "create", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "delete", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "submit", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "cancel", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "amend", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "report", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "export", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "import", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "print", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "email", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "share", 1)

	# Director permissions (read-only)
	add_permission("Material Request", "Director", 0)
	update_permission_property("Material Request", "Director", 0, "read", 1)
	update_permission_property("Material Request", "Director", 0, "report", 1)
	update_permission_property("Material Request", "Director", 0, "export", 1)
	update_permission_property("Material Request", "Director", 0, "print", 1)

	frappe.db.commit()
	print("Material Request permissions configured successfully")
