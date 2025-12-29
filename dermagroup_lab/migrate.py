# Copyright (c) 2024, DeepZide and contributors
# For license information, please see license.txt

import frappe

from dermagroup_lab.patches.customize_material_request_status import (
	execute as customize_material_request_status,
)


def before_migrate():
	"""Execute before migration"""
	pass


def after_migrate():
	"""Execute after migration"""
	from dermagroup_lab.install import (
		ensure_roles_exist,
		setup_material_request_permissions,
		setup_required_permissions,
	)

	print("Customizing Material Request Status...")
	customize_material_request_status()

	print("Verifying roles...")
	ensure_roles_exist()

	print("Setting up Material Request permissions...")
	setup_material_request_permissions()

	print("Setting up required permissions...")
	setup_required_permissions()

	print("Clearing cache...")
	frappe.clear_cache()
	frappe.local.flags.in_migrate = False

	print("Migration completed successfully!")
