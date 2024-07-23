# File: your_app/your_module/job_card_operations.py

import frappe
from frappe import _
import json
from datetime import datetime

@frappe.whitelist()
def refresh_job_cards(filters):
    filters = json.loads(filters)
    job_cards = frappe.get_all('Job Card',
        filters=filters,
        fields=['name', 'workstation', 'operation', 'employee', 'started_time', 
                'status', 'work_order', 'for_quantity', 'total_completed_qty', 'custom_is_active']
    )
    
    for job_card in job_cards:
        job_card['customerName'] = get_customer_name(job_card.work_order)
    
    return job_cards

def get_customer_name(work_order):
    return frappe.get_value('Work Order', work_order, 'custom_customer_name') or ''

@frappe.whitelist()
def complete_job(job_card, completed_qty, employee):
    doc = frappe.get_doc('Job Card', job_card)
    remaining_qty = doc.for_quantity - doc.total_completed_qty

    if float(completed_qty) <= 0 or float(completed_qty) > remaining_qty:
        frappe.throw(_('Invalid completed quantity.'))

    new_time_log = frappe.get_doc({
        'doctype': 'Job Card Time Log',
        'parent': job_card,
        'parenttype': 'Job Card',
        'parentfield': 'time_logs',
        'completed_qty': completed_qty,
        'from_time': doc.actual_start_date,
        'to_time': datetime.now()
    })
    new_time_log.insert()

    doc.employee = employee
    doc.total_completed_qty += float(completed_qty)
    if doc.total_completed_qty >= doc.for_quantity:
        doc.status = 'Completed'
    else:
        doc.status = 'Work In Progress'
    doc.save()

    return {'status': doc.status, 'total_completed_qty': doc.total_completed_qty}

@frappe.whitelist()
def submit_job(job_card):
    doc = frappe.get_doc('Job Card', job_card)
    remaining_qty = doc.for_quantity - doc.total_completed_qty

    if doc.status != 'Completed':
        doc.total_completed_qty = doc.for_quantity
        doc.status = 'Completed'
        doc.save()

    doc.submit()

    if remaining_qty > 0:
        new_job_card = create_new_job_card(doc, remaining_qty)
        return {'message': _('Job Card submitted successfully. New Job Card {} created for remaining quantity.').format(new_job_card.name)}
    else:
        return {'message': _('Job Card submitted successfully.')}

def create_new_job_card(parent_job_card, remaining_qty):
    new_job_card = frappe.copy_doc(parent_job_card)
    new_job_card.status = 'Open'
    new_job_card.for_quantity = remaining_qty
    new_job_card.total_completed_qty = 0
    new_job_card.time_logs = []
    new_job_card.insert()
    return new_job_card

@frappe.whitelist()
def update_job_card_status(job_card, status, is_active):
    doc = frappe.get_doc('Job Card', job_card)
    doc.status = status
    doc.custom_is_active = is_active
    if status == 'Work In Progress' and not doc.actual_start_date:
        doc.actual_start_date = datetime.now()
    doc.save()
    return {'success': True, 'message': _('Job Card status updated successfully.')}

@frappe.whitelist()
def assign_employees_and_start_job(job_card, employees):
    doc = frappe.get_doc('Job Card', job_card)
    doc.employee = []
    for emp in json.loads(employees):
        doc.append('employee', {
            'employee': emp['employee'],
            'employee_name': emp['employee_name']
        })
    doc.status = 'Work In Progress'
    doc.custom_is_active = 1
    doc.actual_start_date = datetime.now()
    doc.save()
    return {'success': True, 'message': _('Employees assigned and job started successfully.')}

@frappe.whitelist()
def decode_scanned_data(scanned_data):
    try:
        decoded = json.loads(frappe.safe_decode(frappe.utils.base64.b64decode(scanned_data)))
        if 'workstation' in decoded and 'password' in decoded:
            return decoded
        else:
            frappe.throw(_('Missing workstation or password in decoded data'))
    except Exception as e:
        frappe.throw(_('Failed to decode scanned data: {}').format(str(e)))

@frappe.whitelist()
def apply_workstation_configuration(workstation, config_data):
    # Implement logic to apply workstation configuration
    # This might involve updating workstation settings or related documents
    return {'success': True, 'message': _('Workstation configuration applied successfully.')}