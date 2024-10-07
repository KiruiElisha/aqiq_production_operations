
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



from frappe import _

@frappe.whitelist()
def get_material_request_details(job_card_name):
    try:
        job_card = frappe.get_doc("Job Card", job_card_name)
        
        if job_card.status == "Material Transferred":
            return {"hasMaterialRequest": True, "hasReceivedQty": True}

        # Check for Material Request
        material_requests = frappe.get_all("Material Request", 
                                           filters={"job_card": job_card_name},
                                           fields=["name"])
        
        has_material_request = len(material_requests) > 0
        has_received_qty = False

        if has_material_request:
            mr_items = frappe.get_all("Material Request Item",
                                      filters={"parent": material_requests[0].name},
                                      fields=["received_qty"])
            has_received_qty = any(item.received_qty > 0 for item in mr_items)

        # Check for Stock Entry against the Job Card
        stock_entries = frappe.get_all("Stock Entry",
                                       filters={
                                           "job_card": job_card_name,
                                           "docstatus": 1,
                                           "stock_entry_type": "Material Transfer for Manufacture"
                                       },
                                       fields=["name"])
        
        has_stock_entry = len(stock_entries) > 0

        # If there's a stock entry, we consider materials as transferred
        if has_stock_entry:
            has_received_qty = True

        return {
            "success": True,
            "hasMaterialRequest": has_material_request or has_stock_entry,
            "hasReceivedQty": has_received_qty
        }

    except frappe.DoesNotExistError:
        frappe.log_error(f"Job Card {job_card_name} not found")
        return {
            "success": False,
            "error": _("Job Card not found")
        }
    except Exception as e:
        frappe.log_error(f"Error fetching Material Request details: {str(e)}")
        return {
            "success": False,
            "error": _("An error occurred while fetching Material Request details")
        }