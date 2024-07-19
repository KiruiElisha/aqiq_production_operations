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