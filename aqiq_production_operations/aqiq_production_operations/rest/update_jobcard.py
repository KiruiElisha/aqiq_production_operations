
import frappe
from frappe.model.document import Document

@frappe.whitelist()
def update_job_card_status(job_card, status, is_active):
    try:
        job_card_doc = frappe.get_doc("Job Card", job_card)
        job_card_doc.flags.ignore_permissions = True

        job_card_doc.status = status
        job_card_doc.custom_is_active = is_active


        job_card_doc.save()
        frappe.db.commit()

        return {"success": True, "message": "Job Card status updated successfully"}
    except frappe.ValidationError as e:
        frappe.db.rollback()
        return {"success": False, "message": str(e)}
    except Exception as e:
        frappe.db.rollback()
        return {"success": False, "message": "An error occurred while updating the Job Card status"}


@frappe.whitelist()
def update_job_progress(job_card, completed_qty):
    try:
        job_card_doc = frappe.get_doc("Job Card", job_card)
        job_card_doc.flags.ignore_permissions = True

        qty_to_manufacture = job_card_doc.for_quantity
        total_completed_qty = job_card_doc.total_completed_qty or 0
        new_total_completed_qty = total_completed_qty + completed_qty

        if new_total_completed_qty > qty_to_manufacture:
            frappe.throw(_("Completed quantity cannot exceed quantity to manufacture"))

        new_status = "Completed" if new_total_completed_qty >= qty_to_manufacture else "Work In Progress"

        time_log = frappe.get_doc({
            "doctype": "Time Log",
            "job_card_id": job_card,
            "start_time": frappe.utils.now_datetime(),
            "complete_time": frappe.utils.now_datetime(),
            "completed_qty": completed_qty,
            "status": new_status
        })
        time_log.insert()

        job_card_doc.total_completed_qty = new_total_completed_qty
        job_card_doc.status = new_status
        job_card_doc.custom_is_active = 0
        job_card_doc.save()
        frappe.db.commit()

        return {
            "success": True,
            "message": "Job Card and Time Log updated successfully",
            "new_total_completed_qty": new_total_completed_qty,
            "new_status": new_status
        }
    except frappe.ValidationError as e:
        frappe.db.rollback()
        return {"success": False, "message": str(e)}
    except Exception as e:
        frappe.db.rollback()
        return {"success": False, "message": "An error occurred while updating the Job Card progress"}

@frappe.whitelist(allow_guest=True)
def get_job_card_employees(job_card_id):
    try:
        # Fetch the Job Card document
        job_card_doc = frappe.get_doc("Job Card", job_card_id)

        # Extract the list of employees from the custom_employee_list field
        employees = job_card_doc.custom_employee_list or []

        # Map the employees to a simple list of employee IDs
        employee_ids = [emp.employee for emp in employees]

        return {
            "success": True,
            "employees": employee_ids
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_job_card_employees Error")
        return {
            "success": False,
            "message": str(e)
        }