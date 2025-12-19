from enum import Enum


class ApprovalStatus(Enum):
	PENDING_APPROVAL = "Pending Approval"
	UNDER_REVIEW = "Under Review"
	APPROVED = "Approved"
	SENT_TO_SUPPLIER = "Sent to Supplier"
	CONFIRMED = "Confirmed"
	PENDING_DELIVERY = "Pending Delivery"
	CANCELLED = "Cancelled"
