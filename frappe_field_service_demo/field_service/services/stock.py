"""Turn the parts used on a visit into an ERPNext stock movement."""

import frappe
from frappe import _


def issue_parts(visit) -> str:
	"""
	Create and submit a Material Issue from the technician's warehouse.

	ERPNext's own stock validation applies, so a visit can't consume parts the
	technician doesn't actually hold.

	Parameters:
		visit (Document, required): The completed Service Visit.

	Returns:
		str: Name of the submitted Stock Entry.
	"""
	warehouse = frappe.db.get_value("Service Technician", visit.technician, "warehouse")
	if not warehouse:
		frappe.throw(_("Technician {0} has no warehouse").format(visit.technician))

	stock_entry = frappe.get_doc(
		{
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Issue",
			"purpose": "Material Issue",
			"company": visit.company,
			"from_warehouse": warehouse,
			"remarks": _("Parts used on Service Visit {0}").format(visit.name),
			"items": [
				{
					"item_code": part.item_code,
					"qty": part.qty,
					"s_warehouse": warehouse,
				}
				for part in visit.parts
			],
		}
	)
	stock_entry.flags.ignore_permissions = True
	stock_entry.insert()
	stock_entry.submit()
	return stock_entry.name
