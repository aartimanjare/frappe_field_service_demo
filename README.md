# Frappe Field Service Demo

**Field service management on ERPNext** (Frappe v15 / v16) for businesses that sell maintenance plans: service contracts, automatic visit scheduling, a technician mobile API, and stock that follows the work done.

> A showcase project written from scratch by [Aarti Manjare](https://github.com/aartimanjare) to demonstrate how I design Frappe apps for field operations. It is not taken from any client codebase.

## Features

| Area | What happens |
|---|---|
| **Service plans** | Define duration and visit frequency, e.g. 12 months with a visit every 3 months |
| **Contracts** | Submitting a contract creates every visit it includes; cancelling it cancels visits that haven't started; a daily job marks expired contracts |
| **Scheduling rules** | Calendar-correct month maths (31 Jan + 1 month = 28/29 Feb); a quarterly plan always gets its 4 visits, with the last pulled onto the contract's final day |
| **Visit status flow** | Scheduled → Assigned → In Progress → Completed (or Cancelled). Steps can't be skipped and finished visits are final, whether changed from Desk or the app |
| **Technician API** | My visits, start, add parts, complete with the customer's signature, reschedule. Each call works only on the technician's own visits |
| **Stock** | Completing a visit issues the parts used from the technician's van/bag warehouse (Material Issue) in the same transaction. If stock is short, the visit isn't completed either |
| **Notifications** | A newly assigned technician gets a bell notification and a realtime push (sent only after commit) |

## Flow

```
Service Plan ──▶ Service Contract (submit) ──▶ Service Visits (one per scheduled date)
                                                   │
                     Manager assigns technician ───┤──▶ Notification Log + realtime push
                                                   │
        Technician app: start → add parts → complete (signature)
                                                   │
                                                   ▼
                          Stock Entry (Material Issue, technician warehouse)
```

## What's inside

```
field_service/
├── logic/                    # pure Python, unit-tested without Frappe
│   ├── scheduling.py         # month maths, contract end, visit dates, reschedule window
│   └── visit_status.py       # allowed status transitions
├── services/
│   ├── contracts.py          # create / cancel visits, expire contracts (idempotent)
│   ├── stock.py              # Material Issue for parts used
│   └── notify.py             # Notification Log + realtime push after commit
├── api/v1/technician.py      # mobile API (standard response envelope, ownership checks)
└── doctype/
    ├── service_plan/  service_technician/  service_contract/ (submittable)
    └── service_visit/  service_visit_part/
```

**Design choices**
- **Rules live in one place.** The status flow and scheduling are plain functions, called by both the DocType controller and the API, so Desk and mobile can never disagree.
- **Least privilege for technicians.** The API checks that the visit belongs to the logged-in technician, then saves through the controller, so every business rule still runs.
- **Atomic completion.** The stock movement and the visit status are committed together, or not at all.
- **Indexed queries.** `scheduled_date` and `technician` are indexed for the daily visit lists.

## API

Prefix: `/api/method/frappe_field_service_demo.field_service.api.v1.technician`

| Endpoint | Method | Body |
|---|---|---|
| `.my_visits` | GET | `from_date`, `to_date` (default: today to 7 days ahead) |
| `.start_visit` | POST | `visit` |
| `.add_part` | POST | `visit`, `item_code`, `qty`, `serial_no` |
| `.complete_visit` | POST | `visit`, `signature` (PNG data URL), `notes` |
| `.reschedule` | POST | `visit`, `new_date` |

Every response has the shape `{"status": true, "message": "", "data": …}`.

## Install

```bash
bench get-app https://github.com/aartimanjare/frappe_field_service_demo
bench --site your-site install-app frappe_field_service_demo
```
Create a **Service Plan**, a **Service Technician** (employee, login user, warehouse), then submit a **Service Contract**.

## Tests

```bash
python -m unittest discover -s tests -t . -v
```
CI (GitHub Actions) runs `ruff` and the unit tests on every push.

## Built with

Python · Frappe Framework · ERPNext · MariaDB · GitHub Actions. Developed with AI-assisted tooling (Claude Code) under code-review and testing standards.

## License

MIT
