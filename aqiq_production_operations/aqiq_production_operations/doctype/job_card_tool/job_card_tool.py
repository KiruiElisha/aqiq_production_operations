# Copyright (c) 2024, RONOH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JobCardTool(Document):
	pass


from frappe import _
from frappe.query_builder import DocType

@frappe.whitelist()
def get_job_cards(status, workstations):
    status_list = frappe.parse_json(status)
    workstations_list = frappe.parse_json(workstations)
    
    # Return empty list if workstations is empty or None
    if not workstations_list:
        return []
    
    JobCard = DocType('Job Card')
    
    query = (
        frappe.qb.from_(JobCard)
        .select(
            JobCard.name, JobCard.workstation, JobCard.operation,
            JobCard.started_time, JobCard.status, JobCard.work_order,
            JobCard.for_quantity, JobCard.total_completed_qty, JobCard.actual_start_date,
            JobCard.custom_is_active
        )
        .where(JobCard.status.isin(status_list))
        .where(JobCard.workstation.isin(workstations_list))
    )
    
    result = query.run(as_dict=True)
    
    return result



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
            "hasMaterialRequest": has_material_request or has_stock_entry,
            "hasReceivedQty": has_received_qty
        }

    except Exception as e:
        frappe.log_error(f"Error fetching Material Request details: {str(e)}")
        return {"hasMaterialRequest": False, "hasReceivedQty": False}