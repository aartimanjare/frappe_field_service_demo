"""Contract lifecycle: create visits, cancel open ones, expire old contracts."""

import frappe
from frappe.utils import getdate, today

from ..logic.scheduling import visit_dates

OPEN_STATUSES = ("Scheduled", "Assigned")


def create_visits(contract) -> list[str]:
	"""
	Create one Service Visit per date the contract's plan entitles it to.

	Safe to call twice: if the contract already has visits, nothing is added.

	Parameters:
		contract (Document, required): The submitted Service Contract.

	Returns:
		list[str]: Names of the visits created.
	"""
	if frappe.db.exists("Service Visit", {"contract": contract.name}):
		return []

	plan = frappe.get_cached_doc("Service Plan", contract.plan)
	created = []
	for scheduled_date in visit_dates(
		getdate(contract.start_date), plan.duration_months, plan.visit_interval_months
	):
		visit = frappe.get_doc(
			{
				"doctype": "Service Visit",
				"contract": contract.name,
				"scheduled_date": scheduled_date,
				"status": "Scheduled",
			}
		).insert(ignore_permissions=True)
		created.append(visit.name)
	return created


def cancel_open_visits(contract_name: str) -> None:
	"""
	Cancel the contract's visits that haven't started, through the normal save path.

	Parameters:
		contract_name (str, required): Service Contract name.

	Returns:
		None
	"""
	for name in frappe.get_all(
		"Service Visit", filters={"contract": contract_name, "status": ("in", OPEN_STATUSES)}, pluck="name"
	):
		visit = frappe.get_doc("Service Visit", name)
		visit.status = "Cancelled"
		visit.save(ignore_permissions=True)


def expire_contracts() -> None:
	"""
	Mark active contracts past their end date as Expired (daily job).

	Returns:
		None
	"""
	frappe.db.set_value(
		"Service Contract",
		{"docstatus": 1, "status": "Active", "end_date": ("<", getdate(today()))},
		"status",
		"Expired",
		update_modified=False,
	)
