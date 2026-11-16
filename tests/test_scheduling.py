"""Visit scheduling rules (no Frappe needed)."""

import unittest
from datetime import date

from frappe_field_service_demo.field_service.logic.scheduling import (
	add_months,
	contract_end_date,
	validate_reschedule,
	visit_dates,
)


class TestAddMonths(unittest.TestCase):
	"""add_months()."""

	def test_month_end_is_clamped(self):
		"""31 Jan + 1 month is the last day of February, leap years included."""
		self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))
		self.assertEqual(add_months(date(2028, 1, 31), 1), date(2028, 2, 29))

	def test_crosses_year_boundary(self):
		"""Adding months rolls into the next year."""
		self.assertEqual(add_months(date(2026, 11, 15), 3), date(2027, 2, 15))


class TestContract(unittest.TestCase):
	"""contract_end_date() and visit_dates()."""

	def test_end_date_is_day_before_anniversary(self):
		"""A 12-month contract from 15 Jan ends on 14 Jan next year."""
		self.assertEqual(contract_end_date(date(2026, 1, 15), 12), date(2027, 1, 14))

	def test_quarterly_plan_gets_four_visits(self):
		"""The fourth quarterly visit is pulled back onto the contract's last day."""
		self.assertEqual(
			visit_dates(date(2026, 1, 15), 12, 3),
			[date(2026, 4, 15), date(2026, 7, 15), date(2026, 10, 15), date(2027, 1, 14)],
		)

	def test_uneven_interval_drops_partial_period(self):
		"""Every 5 months in a 12-month plan gives two full intervals."""
		self.assertEqual(visit_dates(date(2026, 1, 15), 12, 5), [date(2026, 6, 15), date(2026, 11, 15)])

	def test_invalid_periods_are_refused(self):
		"""Zero duration or interval raises an error."""
		with self.assertRaises(ValueError):
			visit_dates(date(2026, 1, 1), 12, 0)
		with self.assertRaises(ValueError):
			contract_end_date(date(2026, 1, 1), 0)


class TestReschedule(unittest.TestCase):
	"""validate_reschedule()."""

	TODAY = date(2026, 11, 16)
	END = date(2027, 1, 14)

	def test_date_inside_window_is_accepted(self):
		"""Today and the contract's last day are both allowed."""
		validate_reschedule(self.TODAY, self.TODAY, self.END)
		validate_reschedule(self.END, self.TODAY, self.END)

	def test_past_date_is_refused(self):
		"""A visit can't be moved into the past."""
		with self.assertRaises(ValueError):
			validate_reschedule(date(2026, 11, 15), self.TODAY, self.END)

	def test_date_after_contract_is_refused(self):
		"""A visit can't be moved past the contract end."""
		with self.assertRaises(ValueError):
			validate_reschedule(date(2027, 1, 15), self.TODAY, self.END)


if __name__ == "__main__":
	unittest.main()
