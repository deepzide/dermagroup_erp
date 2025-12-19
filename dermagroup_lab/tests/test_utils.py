from dermagroup_lab.purchasing.validations import check_duplicate_requests
from dermagroup_lab.tests.test_base import TestBase


class TestUtilsCheckDuplicateRequests(TestBase):
	def test_similar_requests_found(self):
		self.create_material_request(item_code=self.test_item, warehouse=self.test_warehouse)
		duplicates = check_duplicate_requests(item_code=self.test_item)
		assert duplicates

	def test_no_similar_requests_found_4_days_ago(self):
		self.create_material_request(
			item_code=self.test_item, warehouse=self.test_warehouse, transaction_days_ago=-4
		)
		duplicates = check_duplicate_requests(item_code=self.test_item)
		assert not duplicates
