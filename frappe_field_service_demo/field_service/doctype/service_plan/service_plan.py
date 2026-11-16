import frappe
from frappe import _
from frappe.model.document import Document


class ServicePlan(Document):
	"""A maintenance plan: how long it runs and how often a technician visits."""

	def validate(self):
		"""Both periods must be positive, and at least one visit must fit in the plan."""
		if self.duration_months <= 0 or self.visit_interval_months <= 0:
			frappe.throw(_("Duration and visit interval must both be at least one month"))
		if self.visit_interval_months > self.duration_months:
			frappe.throw(
				_("Visit interval ({0} months) is longer than the plan ({1} months)").format(
					self.visit_interval_months, self.duration_months
				)
			)
