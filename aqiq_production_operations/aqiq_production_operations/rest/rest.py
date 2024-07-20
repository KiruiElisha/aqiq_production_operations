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
            job_card.append("employee", {
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
        new_job_card.insert()

        new_name = f"{parent_job_card}-1"
        new_job_card.rename(new_name)

        return new_job_card.name
    except Exception as e:
        frappe.log_error(f"Error in create_and_rename_job_card: {str(e)}")
        return None
    



    # your_app/api.py

@frappe.whitelist()
def authenticate_workstation(workstation, password):
    if frappe.db.exists("Workstation", {"name": workstation, "password": password}):
        return {"authenticated": True}
    else:
        return {"authenticated": False}
