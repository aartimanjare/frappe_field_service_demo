import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, now_datetime, today

from ...logic.scheduling import validate_reschedule
from ...logic.visit_status import check_transition
from ...services.notify import notify_technician
from ...services.stock import issue_parts


class ServiceVisit(Document):
	"""
	One maintenance visit.

	The same rules run whether the visit is changed on the Desk form or from
	the technician app, because they live here and in logic/.
	"""

	def validate(self):
		"""Enforce the status flow, the reschedule window and completion requirements."""
		before = self.get_doc_before_save()
		try:
			check_transition(before.status if before else None, self.status)
			if before and getdate(before.scheduled_date) != getdate(self.scheduled_date):
				contract_end = frappe.db.get_value("Service Contract", self.contract, "end_date")
				validate_reschedule(getdate(self.scheduled_date), getdate(today()), getdate(contract_end))
		except ValueError as error:
			frappe.throw(str(error), title=_("Service Visit {0}").format(self.name))

		if self.status in ("Assigned", "In Progress", "Completed") and not self.technician:
			frappe.throw(_("Assign a technician before moving the visit to {0}").format(self.status))
		if self.status == "Completed":
			if not self.customer_signature:
				frappe.throw(_("The customer's signature is required to complete the visit"))
			self.completed_on = self.completed_on or now_datetime()

	def on_update(self):
		"""Issue the parts used once, and tell a newly assigned technician."""
		before = self.get_doc_before_save()
		if self.status == "Completed" and self.parts and not self.stock_entry:
			# Runs in the same transaction as the save: if stock is short, the
			# visit isn't completed either.
			self.db_set("stock_entry", issue_parts(self))
		if self.technician and (not before or before.technician != self.technician):
			notify_technician(self)
