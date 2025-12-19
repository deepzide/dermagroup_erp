import frappe
from frappe.utils import add_days, nowdate

from dermagroup_lab.purchasing.notifications import notify_purchasing_of_material_request
from dermagroup_lab.purchasing.utils import (
	get_stock_projection,
)
from dermagroup_lab.purchasing.validations import check_duplicate_requests


def daily():
	create_stock_minimum_purchase_requests()


def create_stock_minimum_purchase_requests(days_for_duplicates=3):
	reorder_rows = frappe.db.sql(
		"""
		SELECT
			ir.parent AS item_code,
			ir.warehouse AS warehouse,
			ir.warehouse_reorder_level AS reorder_level,
			ir.warehouse_reorder_qty AS reorder_qty,
			i.lead_time_days AS lead_time_days
		FROM
			`tabItem Reorder` ir
		INNER JOIN
			`tabItem` i ON i.name = ir.parent
		WHERE
			i.disabled = 0
			AND i.is_stock_item = 1
			AND ir.material_request_type = 'Purchase'
		""",
		as_dict=True,
	)

	for row in reorder_rows:
		item_code = row.get("item_code")
		warehouse = row.get("warehouse")
		if not item_code or not warehouse:
			continue

		stock_data = get_stock_projection(item_code, warehouse)
		projected_qty = stock_data.get("projected_qty", 0)
		reorder_level = float(row.get("reorder_level") or 0)
		reorder_qty = float(row.get("reorder_qty") or 0)

		if not (reorder_level or reorder_qty):
			continue

		if projected_qty > reorder_level:
			continue

		deficiency = reorder_level - projected_qty
		required_qty = deficiency if deficiency > reorder_qty else reorder_qty

		if required_qty <= 0:
			continue

		duplicates = check_duplicate_requests(item_code, days=days_for_duplicates)
		if duplicates:
			continue

		company = frappe.db.get_value("Warehouse", warehouse, "company")
		if not company:
			company = frappe.db.get_value("Company", {}, "name")
			if not company:
				continue

		mr = frappe.new_doc("Material Request")
		mr.material_request_type = "Purchase"
		mr.company = company
		mr.transaction_date = nowdate()
		lead_time_days = int(row.get("lead_time_days") or 7)
		mr.schedule_date = add_days(nowdate(), lead_time_days)
		mr.auto_created_via_reorder = 1

		mr.append(
			"items",
			{
				"item_code": item_code,
				"qty": required_qty,
				"warehouse": warehouse,
				"schedule_date": add_days(nowdate(), lead_time_days),
			},
		)

		mr.flags.ignore_mandatory = True
		mr.insert()
		mr.submit()
		notify_purchasing_of_material_request(mr)
