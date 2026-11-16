"""Service Visit status machine (no Frappe needed)."""

import unittest

from frappe_field_service_demo.field_service.logic.visit_status import ALLOWED_TRANSITIONS, check_transition


class TestTransitions(unittest.TestCase):
	"""check_transition()."""

	def test_happy_path(self):
		"""Scheduled -> Assigned -> In Progress -> Completed is allowed step by step."""
		path = ["Scheduled", "Assigned", "In Progress", "Completed"]
		for old, new in zip(path, path[1:], strict=False):
			check_transition(old, new)

	def test_new_visit_and_unchanged_status_pass(self):
		"""A new visit (no old status) and a save without a status change are fine."""
		check_transition(None, "Scheduled")
		check_transition("Assigned", "Assigned")

	def test_finished_visits_are_final(self):
		"""Completed and Cancelled visits can't move anywhere."""
		for final in ("Completed", "Cancelled"):
			self.assertEqual(ALLOWED_TRANSITIONS[final], set())
			with self.assertRaises(ValueError):
				check_transition(final, "Scheduled")

	def test_skipping_steps_is_refused(self):
		"""A visit can't jump from Scheduled straight to Completed."""
		with self.assertRaises(ValueError):
			check_transition("Scheduled", "Completed")

	def test_unknown_status_is_refused(self):
		"""Typos in a status are caught."""
		with self.assertRaises(ValueError):
			check_transition("Scheduled", "Done")


if __name__ == "__main__":
	unittest.main()
