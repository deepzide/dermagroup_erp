import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, nowdate


class TestBase(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		"""Set up test users with different roles"""
		super().setUpClass()
		cls.delete_test_records()
		# Create test users if they don't exist
		cls.production_user = cls.create_test_user("production@test.com", "Production Manager")
		cls.purchasing_user = cls.create_test_user("purchasing@test.com", "Purchasing Manager")
		cls.director_user = cls.create_test_user("director@test.com", "Director")
		# Create test item and warehouse
		cls.test_item = cls.create_test_item()
		cls.company = cls.create_test_company()
		cls.test_warehouse = cls.create_test_warehouse()
		cls.test_supplier = cls.create_test_supplier()

	@classmethod
	def create_test_user(cls, email, role):
		"""Create a test user with specified role"""
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": role.replace(" ", "_"),
					"enabled": 1,
					"send_welcome_email": 0,
				}
			)
			user.insert(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", email)

		# Add role if not already assigned
		if not any(r.role == role for r in user.roles):
			user.append("roles", {"role": role})
			user.save(ignore_permissions=True)

		frappe.db.commit()
		return email

	@classmethod
	def create_test_item(cls):
		"""Create a test item for Material Request"""
		item_code = "_Test Item for MR"

		if not frappe.db.exists("Item", item_code):
			item = frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": item_code,
					"item_name": "Test Item for Material Request",
					"item_group": "Raw Material",
					"stock_uom": "Nos",
					"is_stock_item": 1,
				}
			)
			item.insert(ignore_permissions=True)
			frappe.db.commit()

		return item_code

	@classmethod
	def create_test_company(cls):
		"""Create a test company"""
		company_name = "_Test Company"
		if not frappe.db.exists("Company", company_name):
			company = frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": "_Test Company",
					"country": "Spain",
					"default_currency": "USD",
				}
			)
			company.insert(ignore_permissions=True, ignore_links=True)
			frappe.db.commit()

		return company_name

	@classmethod
	def create_test_warehouse(cls):
		"""Create a test warehouse"""
		warehouse_name = "_Test Warehouse for MR - _TC"

		if not frappe.db.exists("Warehouse", warehouse_name):
			warehouse = frappe.get_doc(
				{
					"doctype": "Warehouse",
					"warehouse_name": warehouse_name,
					"company": cls.company,
				}
			)
			warehouse.insert(ignore_permissions=True, ignore_links=True)
			frappe.db.commit()

		return warehouse.name

	@classmethod
	def create_test_supplier(cls):
		"""Create a test supplier"""
		supplier_name = "_Test Supplier for MR"

		if not frappe.db.exists("Supplier", supplier_name):
			supplier = frappe.get_doc(
				{
					"doctype": "Supplier",
					"supplier_name": supplier_name,
					"supplier_group": "Local",
					"email_id": "supplier@test.com",
				}
			)
			supplier.insert(ignore_permissions=True, ignore_links=True)
			frappe.db.commit()

		return supplier_name

	def create_material_request(self, item_code, warehouse, transaction_days_ago=0, user=None):
		"""Helper to create a Material Request"""
		frappe.set_user(user or "Administrator")
		transaction_date = add_days(nowdate(), transaction_days_ago)

		mr = frappe.get_doc(
			{
				"doctype": "Material Request",
				"material_request_type": "Purchase",
				"transaction_date": transaction_date,
				"schedule_date": add_days(nowdate(), 7),
				"company": self.create_test_company(),
				"items": [
					{
						"item_code": item_code,
						"qty": 10,
						"uom": "Nos",
						"warehouse": warehouse,
						"schedule_date": add_days(nowdate(), 7),
					}
				],
			}
		)
		mr.insert(ignore_links=True)
		mr.submit()
		frappe.db.commit()

		return mr.name

	@classmethod
	def tearDownClass(cls):
		"""Clean up test data"""
		frappe.set_user("Administrator")
		cls.delete_test_records()
		super().tearDownClass()

	@classmethod
	def delete_test_records(cls):
		# Delete test Material Requests
		frappe.db.sql("""
			DELETE FROM `tabMaterial Request`
		""")

		frappe.db.sql("""
			DELETE FROM `tabWarehouse`
			WHERE name LIKE '%_Test%'
		""")
		frappe.db.sql("""
			DELETE FROM `tabItem`
			WHERE item_code LIKE '%_Test%'
		""")

		frappe.delete_doc_if_exists("User", "director@test.com")
		frappe.delete_doc_if_exists("User", "purchasing@test.com")
		frappe.delete_doc_if_exists("User", "production@test.com")
		frappe.db.commit()
