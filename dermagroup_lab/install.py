# Copyright (c) 2024, DeepZide and contributors
# For license information, please see license.txt

import frappe
from frappe.permissions import add_permission, update_permission_property

DERMAGROUP_LAB_ROLES = [
	"Production Manager",  # Producción
	"Purchasing Manager",  # Compras
	"Director",  # Dirección
	"Reception Manager",  # Recepción
	"Quality Manager",  # Calidad
]


def after_install():
	"""
	Configure custom permissions after app installation
	"""
	ensure_roles_exist()
	setup_material_request_permissions()
	setup_required_permissions()


def ensure_roles_exist():
	for role_name in DERMAGROUP_LAB_ROLES:
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


def setup_required_permissions():
	"""
	Set up permissions for different roles:
	- Production: Can view Suppliers, Warehouses, Companies, and Items
	- Purchasing: Full access to Suppliers, Warehouses, Companies, and Items
	- Director: Read-only access to view data with export/print capabilities
	"""
	# Common doctypes that need role-based permissions
	doctypes = ["Supplier", "Warehouse", "Company", "Item"]

	# Production Manager - Basic read access
	for doctype in doctypes:
		add_permission(doctype, "Production Manager", 0)
		update_permission_property(doctype, "Production Manager", 0, "read", 1)

	# Purchasing Manager - Full access
	for doctype in doctypes:
		add_permission(doctype, "Purchasing Manager", 0)
		update_permission_property(doctype, "Purchasing Manager", 0, "read", 1)
		update_permission_property(doctype, "Purchasing Manager", 0, "write", 1)
		update_permission_property(doctype, "Purchasing Manager", 0, "create", 1)
		update_permission_property(doctype, "Purchasing Manager", 0, "delete", 1)
		update_permission_property(doctype, "Purchasing Manager", 0, "export", 1)
		update_permission_property(doctype, "Purchasing Manager", 0, "print", 1)

	# Director - Read-only with export/print
	for doctype in doctypes:
		add_permission(doctype, "Director", 0)
		update_permission_property(doctype, "Director", 0, "read", 1)
		update_permission_property(doctype, "Director", 0, "export", 1)
		update_permission_property(doctype, "Director", 0, "print", 1)

	frappe.db.commit()
	print("Required permissions configured successfully")


def setup_material_request_permissions():
	"""
	Set up role-based permissions for Material Request:
	- Production: Can create and submit requests
	- Purchasing: Full access to review, edit, send, and confirm
	- Director: Read-only access to view pending requests and costs
	"""
	# Production Manager - Can create and submit requests
	add_permission("Material Request", "Production Manager", 0)
	update_permission_property("Material Request", "Production Manager", 0, "read", 1)
	update_permission_property("Material Request", "Production Manager", 0, "write", 1)
	update_permission_property("Material Request", "Production Manager", 0, "create", 1)
	update_permission_property("Material Request", "Production Manager", 0, "submit", 1)
	update_permission_property("Material Request", "Production Manager", 0, "print", 1)

	# Purchasing Manager - Full access to review, edit, send, and confirm
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
	update_permission_property("Material Request", "Purchasing Manager", 0, "print", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "email", 1)
	update_permission_property("Material Request", "Purchasing Manager", 0, "share", 1)

	# Director - Read-only access to view pending requests and costs
	add_permission("Material Request", "Director", 0)
	update_permission_property("Material Request", "Director", 0, "read", 1)
	update_permission_property("Material Request", "Director", 0, "report", 1)
	update_permission_property("Material Request", "Director", 0, "export", 1)
	update_permission_property("Material Request", "Director", 0, "print", 1)
	# Add view cost center permissions for cost visibility
	update_permission_property("Cost Center", "Director", 0, "read", 1)
	update_permission_property("Cost Center", "Director", 0, "export", 1)
	update_permission_property("Cost Center", "Director", 0, "print", 1)

	frappe.db.commit()
	print("Material Request permissions configured successfully")
