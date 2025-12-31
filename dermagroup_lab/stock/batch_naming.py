import frappe
from frappe.model.naming import make_autoname
from frappe.utils import getdate, today


def autoname_batch(doc, method):
	"""
	Custom autoname for Batch.
	Format: PREFIX-YYYY-MM-.####
	Prefix is fetched from Item Group's 'batch_prefix' field.
	"""
	if not doc.item:
		return

	# Logic to determine prefix
	# 1. Get Item Group
	item_group = frappe.get_cached_value("Item", doc.item, "item_group")
	if not item_group:
		return

	# 2. Get Prefix from Item Group
	# Note: 'batch_prefix' is a custom field on Item Group
	prefix = frappe.db.get_value("Item Group", item_group, "batch_prefix")

	if not prefix:
		# If no prefix configured, fall back to standard naming or do nothing
		# For now, we return to let standard Batch autoname handle it
		return

	# 3. Generate Name
	# Pattern: PREFIX-YYYY-MM-.####
	current_date = getdate(today())
	year = current_date.year
	month = f"{current_date.month:02d}"

	# make_autoname with #### handles the sequence
	series = f"{prefix}-{year}-{month}-.####"

	doc.name = make_autoname(series)
