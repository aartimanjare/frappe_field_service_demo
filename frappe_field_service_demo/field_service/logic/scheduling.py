"""Visit scheduling rules.

Pure functions (only the standard library), so they are unit-tested without a
Frappe site and reused by the controllers and the technician API.
"""

import calendar
from datetime import date, timedelta


def add_months(start: date, months: int) -> date:
	"""
	Add calendar months, clamping to the last day of shorter months.

	Parameters:
		start (date, required): The starting date.
		months (int, required): Months to add (may be negative).

	Returns:
		date: e.g. 31 Jan + 1 month -> 28/29 Feb.
	"""
	month_index = start.month - 1 + months
	year, month = start.year + month_index // 12, month_index % 12 + 1
	day = min(start.day, calendar.monthrange(year, month)[1])
	return date(year, month, day)


def contract_end_date(start: date, duration_months: int) -> date:
	"""
	Return the last day a contract covers.

	Parameters:
		start (date, required): Contract start date.
		duration_months (int, required): Contract length in months (> 0).

	Returns:
		date: The day before start + duration, e.g. 1 Jan + 12 months -> 31 Dec.
	"""
	if duration_months <= 0:
		raise ValueError("Duration must be at least one month")
	return add_months(start, duration_months) - timedelta(days=1)


def visit_dates(start: date, duration_months: int, interval_months: int) -> list[date]:
	"""
	List the maintenance visit dates a contract entitles the customer to.

	A plan gets duration // interval visits, one every interval after the
	start. The last one can land on the day after the contract ends (start + 12
	months), so it is pulled back to the contract's final day: a 12-month
	quarterly plan always gets its 4 visits.

	Parameters:
		start (date, required): Contract start date.
		duration_months (int, required): Contract length in months.
		interval_months (int, required): Months between visits (> 0).

	Returns:
		list[date]: Visit dates in order.
	"""
	if interval_months <= 0:
		raise ValueError("Visit interval must be at least one month")
	end = contract_end_date(start, duration_months)
	count = duration_months // interval_months
	return [min(add_months(start, step * interval_months), end) for step in range(1, count + 1)]


def validate_reschedule(new_date: date, today: date, contract_end: date) -> None:
	"""
	Check a requested new visit date.

	Parameters:
		new_date (date, required): The date asked for.
		today (date, required): Today's date (passed in, so tests can fix it).
		contract_end (date, required): Last day of the contract.

	Raises:
		ValueError: When the date is in the past or after the contract ends.
	"""
	if new_date < today:
		raise ValueError("A visit can't be moved into the past")
	if new_date > contract_end:
		raise ValueError(f"The contract ends on {contract_end.isoformat()}")
