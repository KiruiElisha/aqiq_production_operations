import frappe
from frappe import _
from datetime import datetime

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": _("Job Card ID"), "fieldname": "name", "fieldtype": "Link", "options": "Job Card", "width": 120},
        {"label": _("Work Order"), "fieldname": "work_order", "fieldtype": "Link", "options": "Work Order", "width": 120},
        {"label": _("Production Item"), "fieldname": "production_item", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": _("Operation"), "fieldname": "operation", "fieldtype": "Data", "width": 120},
        # {"label": _("Workstation"), "fieldname": "workstation", "fieldtype": "Link", "options": "Workstation", "width": 120},
        # {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        # {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        # {"label": _("Expected Start Date"), "fieldname": "expected_start_date", "fieldtype": "Datetime", "width": 150},
        # {"label": _("Expected End Date"), "fieldname": "expected_end_date", "fieldtype": "Datetime", "width": 150},
        # {"label": _("Actual Start Date"), "fieldname": "actual_start_date", "fieldtype": "Datetime", "width": 150},
        # {"label": _("Actual End Date"), "fieldname": "actual_end_date", "fieldtype": "Datetime", "width": 150},
        {"label": _("For Quantity"), "fieldname": "for_quantity", "fieldtype": "Float", "width": 100},
        {"label": _("Completed Quantity"), "fieldname": "total_completed_qty", "fieldtype": "Float", "width": 120},
        {"label": _("Process Loss Quantity"), "fieldname": "process_loss_qty", "fieldtype": "Float", "width": 150},
        {"label": _("Time Required (mins)"), "fieldname": "time_required", "fieldtype": "Float", "width": 150},
        {"label": _("Actual Time Taken (mins)"), "fieldname": "total_time_in_mins", "fieldtype": "Float", "width": 150},
        {"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
    ]

def get_data(filters):
    conditions = get_conditions(filters)
    data = frappe.db.sql("""
        SELECT 
            jc.name, jc.work_order, jc.production_item, jc.operation, jc.workstation,
            jc.status, jc.posting_date, jc.expected_start_date, jc.expected_end_date,
            jc.actual_start_date, jc.actual_end_date, jc.for_quantity,
            jc.total_completed_qty, jc.process_loss_qty, jc.time_required,
            jc.total_time_in_mins, jctl.employee
        FROM 
            `tabJob Card` jc
        LEFT JOIN
            `tabJob Card Time Log` jctl ON jc.name = jctl.parent
        WHERE
            {conditions}
        ORDER BY
            jc.posting_date DESC, jc.name
    """.format(conditions=conditions), filters, as_dict=1)
    
    return data

def get_conditions(filters):
    conditions = []
    if filters.get("from_date"):
        conditions.append("jc.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("jc.posting_date <= %(to_date)s")
    if filters.get("work_order"):
        conditions.append("jc.work_order = %(work_order)s")
    if filters.get("production_item"):
        conditions.append("jc.production_item = %(production_item)s")
    if filters.get("operation"):
        conditions.append("jc.operation = %(operation)s")
    if filters.get("workstation"):
        conditions.append("jc.workstation = %(workstation)s")
    if filters.get("status"):
        conditions.append("jc.status = %(status)s")
    if filters.get("employee"):
        conditions.append("jctl.employee = %(employee)s")
    
    return " AND ".join(conditions)

def get_chart_data(data):
    labels = []
    completed_qty = []
    process_loss_qty = []

    for entry in data:
        labels.append(entry.get("name"))
        completed_qty.append(entry.get("total_completed_qty"))
        process_loss_qty.append(entry.get("process_loss_qty"))

    return {
        "data": {
            "labels": labels,
            "datasets": [
                {"name": "Completed Quantity", "values": completed_qty},
                {"name": "Process Loss Quantity", "values": process_loss_qty}
            ]
        },
        "type": "bar",
        "colors": ["#00FF00", "#FF0000"]
    }