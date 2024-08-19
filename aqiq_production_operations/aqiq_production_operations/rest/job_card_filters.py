import frappe
from frappe import _
import json
import frappe
from frappe import _
import json

@frappe.whitelist()
def save_user_filters(filters):
    try:
        # Ensure filters are in JSON string format
        if isinstance(filters, dict):
            filters = json.dumps(filters)
        
        filters = json.loads(filters)

        user = frappe.session.user
        filters_doc_data = {
            "doctype": "Job Card Tool User Filters",
            "user": user,
            "job_card_status": json.dumps(filters.get("job_card_status", [])),
            "filtered_workstations": filters.get("filtered_workstations", "")
        }

        existing_filters = frappe.get_all("Job Card Tool User Filters", filters={"user": user})

        if existing_filters:
            filters_doc = frappe.get_doc("Job Card Tool User Filters", existing_filters[0].name)
            filters_doc.update(filters_doc_data)
            filters_doc.flags.ignore_permissions = True
            filters_doc.save()
        else:
            filters_doc = frappe.get_doc(filters_doc_data)
            filters_doc.insert()

        return {"success": True}
    except frappe.exceptions.ValidationError:
        frappe.db.rollback()
        save_user_filters(filters)


@frappe.whitelist()
def get_user_filters():
    user = frappe.session.user
    filters_doc = frappe.get_all("Job Card Tool User Filters", filters={"user": user}, limit=1)
    if filters_doc:
        filters_doc = frappe.get_doc("Job Card Tool User Filters", filters_doc[0].name)
        return {
            "job_card_status": json.loads(filters_doc.job_card_status),
            "filtered_workstations": filters_doc.filtered_workstations
        }
    return {}

@frappe.whitelist()
def clear_user_filters():
    user = frappe.session.user
    filters_doc = frappe.get_all("Job Card Tool User Filters", filters={"user": user}, limit=1)
    if filters_doc:
        filters_doc = frappe.get_doc("Job Card Tool User Filters", filters_doc[0].name)
        filters_doc.delete()

    return {"success": True}
