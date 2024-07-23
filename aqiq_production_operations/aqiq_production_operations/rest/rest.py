import frappe
import json

@frappe.whitelist()
def set_job_card_employees(job_card_name, employees):
    try:
        job_card = frappe.get_doc("Job Card", job_card_name)
        
        # If employees is a string, parse it to a list of dictionaries
        if isinstance(employees, str):
            employees = json.loads(employees)
        
        # Clear existing employees
        job_card.employee = []
        
        # Add new employees
        for emp in employees:
            job_card.append("custom_employee_list", {
                "employee": emp.get("employee"),
                "employee_name": emp.get("employee_name")
            })
        
        job_card.save()
        frappe.db.commit()
        return "Success"
    
    except Exception as e:
        frappe.log_error(f"Error in set_job_card_employees: {str(e)}")
        return f"Error: {str(e)}"
    

@frappe.whitelist()
def create_and_rename_job_card(parent_job_card, remaining_qty):
    try:
        parent_doc = frappe.get_doc("Job Card", parent_job_card)
        new_job_card = frappe.copy_doc(parent_doc)
        new_job_card.status = 'Open'
        new_job_card.custom_is_active = False
        new_job_card.for_quantity = float(remaining_qty)
        new_job_card.total_completed_qty = 0
        new_job_card.time_logs = []
        new_job_card.scrap_items = []
        new_job_card.docstatus = 0
        new_job_card.custom_employee_list = []
        new_job_card.insert()
        

        new_name = f"{parent_job_card}-1"
        new_job_card.rename(new_name)

        return new_job_card.name
    except Exception as e:
        frappe.log_error(f"Error in create_and_rename_job_card: {str(e)}")
        return None



import frappe
from frappe import _
from frappe.utils import now_datetime
import json

@frappe.whitelist()
def start_job(job_card):
    try:
        job_card_doc = frappe.get_doc("Job Card", job_card)
        employees = job_card_doc.get("custom_employee_list", [])
        
        for employee_row in employees:
            make_time_log(job_card, employee_row.employee)
        
        job_card_doc.status = "Work In Progress"
        job_card_doc.custom_is_active = True
        job_card_doc.time_logs = []
        job_card_doc.save()
        
        return "Success"
    except Exception as e:
        frappe.log_error(f"Error starting job: {str(e)}")
        return "Error"

def make_time_log(job_card, employee):
    args = {
        "job_card_id": job_card,
        "employee": employee,
        "completed_qty": 0,
        "complete_time": now_datetime()
    }
    frappe.get_doc({
        "doctype": "Job Card Time Log",
        "parent": job_card,
        "parenttype": "Job Card",
        "parentfield": "time_logs",
        **args
    }).insert()

@frappe.whitelist()
def get_workstation_employees(workstation):
    workstation_doc = frappe.get_doc("Workstation", workstation)
    return workstation_doc.get("custom_employee_details", [])

@frappe.whitelist()
def set_job_card_employees_and_start(job_card_name, employees):
    try:
        employees = json.loads(employees)
        job_card = frappe.get_doc("Job Card", job_card_name)
        job_card.custom_employee_list = []
        
        for emp in employees:
            job_card.append("custom_employee_list", {
                "employee": emp["employee"],
                "employee_name": emp["employee_name"]
            })
        
        job_card.status = "Work In Progress"
        job_card.custom_is_active = True
        job_card.time_logs = []
        job_card.save()
        
        for emp in employees:
            make_time_log(job_card_name, emp["employee"])
        
        return "Success"
    except Exception as e:
        frappe.log_error(f"Error setting job card employees and starting: {str(e)}")
        return "Error"
