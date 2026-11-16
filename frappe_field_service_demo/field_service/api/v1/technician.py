"""Technician mobile app API.

Every call works only on the logged-in technician's own visits. Ownership is
checked here, then the save runs with ignore_permissions so technicians don't
need broad Desk rights; all business rules still run in the Service Visit
controller.
"""

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, today

from ..response import ok

VISIT_FIELDS = ["name", "customer", "scheduled_date", "status", "contract"]


@frappe.whitelist(methods=["GET"])
def my_visits(from_date: str | None = None, to_date: str | None = None) -> dict:
	"""
	List the technician's visits in a date range (default: today to 7 days ahead).

	Endpoint: /api/method/frappe_field_service_demo.field_service.api.v1.technician.my_visits
	Method: GET

	Parameters:
		from_date (str, optional): ISO date, default today.
		to_date (str, optional): ISO date, default today + 7 days.

	Returns:
		dict: {"status": true, "message": "", "data": [{"name", "customer", "scheduled_date", "status", "contract", "serial_no"}]}
	"""
	technician = _current_technician()
	start = getdate(from_date or today())
	end = getdate(to_date or add_days(today(), 7))
	if end < start:
		frappe.throw(_("to_date can't be before from_date"))

	visits = frappe.get_all(
		"Service Visit",
		filters={"technician": technician, "scheduled_date": ("between", [start, end])},
		fields=VISIT_FIELDS,
		order_by="scheduled_date asc",
	)
	serials = (
		dict(
			frappe.get_all(
				"Service Contract",
				filters={"name": ("in", list({visit.contract for visit in visits}))},
				fields=["name", "serial_no"],
				as_list=True,
			)
		)
		if visits
		else {}
	)
	for visit in visits:
		visit.serial_no = serials.get(visit.contract)
	return ok(visits)


@frappe.whitelist(methods=["POST"])
def start_visit(visit: str) -> dict:
	"""
	Mark an assigned visit as In Progress.

	Endpoint: /api/method/frappe_field_service_demo.field_service.api.v1.technician.start_visit
	Method: POST

	Parameters:
		visit (str, required): Service Visit name.

	Returns:
		dict: {"status": true, "message": "", "data": {"name", "status"}}
	"""
	doc = _own_visit(visit)
	doc.status = "In Progress"
	doc.save(ignore_permissions=True)
	return ok({"name": doc.name, "status": doc.status})


@frappe.whitelist(methods=["POST"])
def add_part(visit: str, item_code: str, qty: float = 1, serial_no: str | None = None) -> dict:
	"""
	Record a spare part or consumable used on a visit in progress.

	Endpoint: /api/method/frappe_field_service_demo.field_service.api.v1.technician.add_part
	Method: POST

	Parameters:
		visit (str, required): Service Visit name.
		item_code (str, required): The Item used.
		qty (float, optional): Quantity, default 1.
		serial_no (str, optional): Serial number of the part, if tracked.

	Returns:
		dict: {"status": true, "message": "", "data": {"parts": [{"item_code", "qty", "serial_no"}]}}
	"""
	if not isinstance(item_code, str) or not frappe.db.exists("Item", item_code):
		frappe.throw(_("Unknown item {0}").format(item_code))
	if flt(qty) <= 0:
		frappe.throw(_("Quantity must be greater than zero"))

	doc = _own_visit(visit)
	if doc.status != "In Progress":
		frappe.throw(_("Start the visit before adding parts"))
	doc.append("parts", {"item_code": item_code, "qty": flt(qty), "serial_no": serial_no})
	doc.save(ignore_permissions=True)
	return ok(
		{"parts": [{"item_code": p.item_code, "qty": p.qty, "serial_no": p.serial_no} for p in doc.parts]}
	)


@frappe.whitelist(methods=["POST"])
def complete_visit(visit: str, signature: str, notes: str | None = None) -> dict:
	"""
	Complete a visit with the customer's signature; the parts used are issued from stock.

	Endpoint: /api/method/frappe_field_service_demo.field_service.api.v1.technician.complete_visit
	Method: POST

	Parameters:
		visit (str, required): Service Visit name.
		signature (str, required): The customer's signature as a data URL (image/png).
		notes (str, optional): Work notes.

	Returns:
		dict: {"status": true, "message": "", "data": {"name", "status", "stock_entry"}}
	"""
	if not isinstance(signature, str) or not signature.startswith("data:image/"):
		frappe.throw(_("signature must be an image data URL"))

	doc = _own_visit(visit)
	doc.customer_signature = signature
	if notes:
		doc.notes = notes
	doc.status = "Completed"
	doc.save(ignore_permissions=True)
	doc.reload()
	return ok({"name": doc.name, "status": doc.status, "stock_entry": doc.stock_entry})


@frappe.whitelist(methods=["POST"])
def reschedule(visit: str, new_date: str) -> dict:
	"""
	Move one of the technician's visits to another date inside the contract.

	Endpoint: /api/method/frappe_field_service_demo.field_service.api.v1.technician.reschedule
	Method: POST

	Parameters:
		visit (str, required): Service Visit name.
		new_date (str, required): ISO date; not in the past, not after the contract ends.

	Returns:
		dict: {"status": true, "message": "", "data": {"name", "scheduled_date"}}
	"""
	doc = _own_visit(visit)
	if doc.status not in ("Scheduled", "Assigned"):
		frappe.throw(_("Only visits that haven't started can be rescheduled"))
	doc.scheduled_date = getdate(new_date)
	doc.save(ignore_permissions=True)
	return ok({"name": doc.name, "scheduled_date": str(doc.scheduled_date)})


def _current_technician() -> str:
	"""Return the active Service Technician linked to the session user, or stop."""
	technician = frappe.db.get_value("Service Technician", {"user": frappe.session.user, "active": 1}, "name")
	if not technician:
		frappe.throw(_("You are not set up as an active technician"), frappe.PermissionError)
	return technician


def _own_visit(name: str):
	"""Load a visit, refusing anything not assigned to the session's technician."""
	if not isinstance(name, str) or not name:
		frappe.throw(_("visit must be a Service Visit name"))
	technician = _current_technician()
	if frappe.db.get_value("Service Visit", name, "technician") != technician:
		frappe.throw(_("Visit {0} is not assigned to you").format(name), frappe.PermissionError)
	return frappe.get_doc("Service Visit", name)
