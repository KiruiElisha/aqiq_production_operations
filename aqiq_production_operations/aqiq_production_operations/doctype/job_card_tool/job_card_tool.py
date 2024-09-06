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
    
    JobCard = DocType('Job Card')
    
    query = (
        frappe.qb.from_(JobCard)
        .select(
            JobCard.name, JobCard.workstation, JobCard.operation,
            JobCard.started_time, JobCard.status, JobCard.work_order,
            JobCard.for_quantity, JobCard.total_completed_qty,JobCard.actual_start_date,
            JobCard.custom_is_active
        )
        .where(JobCard.status.isin(status_list))
        .where(JobCard.workstation.isin(workstations_list))
    )
    
    result = query.run(as_dict=True)
    
    return result