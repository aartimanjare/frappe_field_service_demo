"""Tell technicians about new work: a bell notification plus a realtime push for the app."""

import frappe
from frappe import _
from frappe.utils import formatdate


def notify_technician(visit) -> None:
	"""
	Notify the visit's technician that it was assigned to them.

	Parameters:
		visit (Document, required): The Service Visit just assigned.

	Returns:
		None
	"""
	user = frappe.db.get_value("Service Technician", visit.technician, "user")
	if not user:
		return

	subject = _("New visit {0} for {1} on {2}").format(
		visit.name, visit.customer, formatdate(visit.scheduled_date)
	)
	frappe.get_doc(
		{
			"doctype": "Notification Log",
			"for_user": user,
			"type": "Alert",
			"document_type": "Service Visit",
			"document_name": visit.name,
			"subject": subject,
		}
	).insert(ignore_permissions=True)

	# after_commit: the app only hears about the visit once it really exists.
	frappe.publish_realtime(
		"service_visit_assigned",
		{"visit": visit.name, "scheduled_date": str(visit.scheduled_date), "customer": visit.customer},
		user=user,
		after_commit=True,
	)
