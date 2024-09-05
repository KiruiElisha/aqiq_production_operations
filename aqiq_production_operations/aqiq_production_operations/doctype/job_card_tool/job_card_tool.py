# Copyright (c) 2024, RONOH and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class JobCardTool(Document):
	pass


from frappe import _
from frappe.utils.caching import redis_cache

@frappe.whitelist()
@redis_cache(ttl=300)  # Cache for 5 minutes
def get_job_cards(status, workstations):
    status_list = frappe.parse_json(status)
    workstations_list = frappe.parse_json(workstations)
    
    cache_key = f"job_cards:{','.join(status_list)}:{','.join(workstations_list)}"
    
    # Try to get results from cache
    cached_result = frappe.cache().get_value(cache_key)
    if cached_result:
        return cached_result
    
    # If not in cache, fetch from database
    result = frappe.get_all('Job Card',
        filters={
            'status': ('in', status_list),
            'workstation': ('in', workstations_list)
        },
        fields=['name', 'workstation', 'operation', 'started_time', 
                'status', 'work_order', 'for_quantity', 'total_completed_qty', 'custom_is_active']
    )
    
    # Store result in cache
    frappe.cache().set_value(cache_key, result)
    
    return result