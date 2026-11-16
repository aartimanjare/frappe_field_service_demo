import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from ...logic.scheduling import contract_end_date
from ...services.contracts import cancel_open_visits, create_visits


class ServiceContract(Document):
	"""A customer's maintenance contract; submitting it creates all its visits."""

	def validate(self):
		"""Work out the end date from the plan."""
		duration = frappe.db.get_value("Service Plan", self.plan, "duration_months")
		if not duration:
			frappe.throw(_("Service Plan {0} has no duration").format(self.plan))
		self.end_date = contract_end_date(getdate(self.start_date), duration)

	def on_submit(self):
		"""Activate the contract and schedule every visit it includes."""
		create_visits(self)
		self.db_set("status", "Active")

	def on_cancel(self):
		"""Cancel visits that haven't started; completed work stays on record."""
		cancel_open_visits(self.name)
		self.db_set("status", "Cancelled")
