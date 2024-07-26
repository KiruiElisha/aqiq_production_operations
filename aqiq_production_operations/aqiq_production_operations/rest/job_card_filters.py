import frappe

@frappe.whitelist()
def save_job_card_filters(filters):
    frappe.cache().hset("job_card_filters", frappe.session.user, filters)

@frappe.whitelist()
def load_job_card_filters():
    return frappe.cache().hget("job_card_filters", frappe.session.user)