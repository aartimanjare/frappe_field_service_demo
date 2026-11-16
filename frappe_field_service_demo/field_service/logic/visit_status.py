"""Service Visit status machine.

Kept as data plus one check, so the allowed moves are readable at a glance
and the same rule protects the Desk form and the technician API.
"""

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
	"Scheduled": {"Assigned", "Cancelled"},
	"Assigned": {"In Progress", "Scheduled", "Cancelled"},
	"In Progress": {"Completed", "Assigned"},
	"Completed": set(),
	"Cancelled": set(),
}


def check_transition(old_status: str | None, new_status: str) -> None:
	"""
	Refuse a status change the process doesn't allow.

	Parameters:
		old_status (str, optional): Status before the change (None for a new visit).
		new_status (str, required): Status being saved.

	Raises:
		ValueError: When the move isn't allowed, e.g. Completed -> Scheduled.
	"""
	if new_status not in ALLOWED_TRANSITIONS:
		raise ValueError(f"Unknown status {new_status}")
	if old_status is None or old_status == new_status:
		return
	if new_status not in ALLOWED_TRANSITIONS.get(old_status, set()):
		raise ValueError(f"A visit can't move from {old_status} to {new_status}")
