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
    

import frappe

@frappe.whitelist()
def create_and_rename_job_card(parent_job_card, remaining_qty):
    try:
        # Fetch the parent job card document
        parent_doc = frappe.get_doc("Job Card", parent_job_card)
        
        # Update the for_quantity in the parent job card to match total_completed_qty
        if parent_doc.docstatus == 1:  # Check if the document is already submitted
            frappe.db.sql("""
                UPDATE `tabJob Card`
                SET for_quantity = %s, process_loss_qty = 0
                WHERE name = %s
            """, (parent_doc.total_completed_qty, parent_job_card))
            
            # Submit the parent job card again
            frappe.db.sql("""
                UPDATE `tabJob Card`
                SET docstatus = 1
                WHERE name = %s
            """, parent_job_card)
        else:
            parent_doc.for_quantity = parent_doc.total_completed_qty
            parent_doc.process_loss = 0  # Set process loss to 0
            parent_doc.save()
            parent_doc.submit()
        
        # Create a copy of the parent job card document
        new_job_card = frappe.copy_doc(parent_doc)
        new_job_card.status = 'Open'
        new_job_card.custom_is_active = False
        
        # Set the remaining quantity for the new job card
        new_job_card.for_quantity = float(remaining_qty)
        new_job_card.total_completed_qty = 0
        new_job_card.time_logs = []
        new_job_card.scrap_items = []
        new_job_card.docstatus = 0
        new_job_card.custom_employee_list = []
        new_job_card.actual_end_date = None
        new_job_card.actual_start_date = None
        new_job_card.total_time_in_mins = 0
        new_job_card.custom_skip_material_request = True

        # Insert the new job card document
        new_job_card.insert()
        
        # Generate the new name
        new_name = f"{parent_job_card}-1"
        
        # Set the new name
        frappe.db.set_value("Job Card", new_job_card.name, "name", new_name)
        
        return new_name
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



@frappe.whitelist()
def validate_job_card_sequence_id(job_card_name):
    job_card = frappe.get_doc("Job Card", job_card_name)

    if job_card.is_corrective_job_card:
        return

    if not (job_card.work_order and job_card.sequence_id):
        frappe.throw(_("Work Order and Sequence ID are required for Job Card {0}").format(job_card_name))

    all_job_cards = frappe.get_all(
        "Job Card",
        filters={"work_order": job_card.work_order},
        fields=["name", "sequence_id", "status", "docstatus", "operation", "total_completed_qty", "for_quantity"],
        order_by="sequence_id, creation"
    )

    sequence_groups = {}
    for jc in all_job_cards:
        if jc.sequence_id not in sequence_groups:
            sequence_groups[jc.sequence_id] = []
        sequence_groups[jc.sequence_id].append(jc)

    current_group = next((group for group in sequence_groups.values() if job_card_name in [jc.name for jc in group]), None)
    if current_group is None:
        frappe.throw(_("Job Card {0} not found in the sequence for Work Order {1}").format(job_card_name, job_card.work_order))

    current_seq_id = current_group[0].sequence_id

    for seq_id in sorted(sequence_groups.keys()):
        if int(seq_id) >= int(current_seq_id):
            break

        prev_group = sequence_groups[seq_id]
        
        # Check if at least one job card in the previous group has some completed quantity
        if not any(prev_job_card.total_completed_qty > 0 for prev_job_card in prev_group):
            frappe.throw(_("At least one Job Card in the previous sequence (Sequence: {0}) must have some completed quantity before starting Job Card {1} (Operation: {2}, Sequence: {3})").format(
                seq_id, job_card_name, job_card.operation, current_seq_id
            ))

    return True


