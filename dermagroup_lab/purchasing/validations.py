import frappe
from frappe.utils import add_days, nowdate


@frappe.whitelist()
def check_duplicate_requests(item_code, supplier=None, days=3):
	"""
	Check for duplicate material requests in the last N days
	Returns: list of similar material requests
	"""
	cutoff_date = add_days(nowdate(), -int(days))

	query = """
		SELECT
			mr.name,
			mr.transaction_date,
			mr.status,
			mri.qty,
			mri.warehouse
		FROM
			`tabMaterial Request` mr
		INNER JOIN
			`tabMaterial Request Item` mri ON mri.parent = mr.name
		WHERE
			mri.item_code = %(item_code)s
		"""
	if supplier:
		query += "AND mr.suggested_supplier = %(supplier)s"
	query += """
		AND mr.transaction_date >= %(cutoff_date)s
		AND mr.docstatus < 2
		AND mr.material_request_type = 'Purchase'
		ORDER BY
			mr.transaction_date DESC"""
	return frappe.db.sql(
		query, {"item_code": item_code, "supplier": supplier, "cutoff_date": cutoff_date}, as_dict=True
	)
