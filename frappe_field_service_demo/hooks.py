app_name = "frappe_field_service_demo"
app_title = "Field Service Demo"
app_publisher = "Aarti Manjare"
app_description = "Service contracts, visit scheduling and a technician API for ERPNext"
app_email = "aartimanjare@gmail.com"
app_license = "mit"

required_apps = ["erpnext"]

# Contracts past their end date stop generating work.
scheduler_events = {
	"daily": [
		"frappe_field_service_demo.field_service.services.contracts.expire_contracts",
	],
}
