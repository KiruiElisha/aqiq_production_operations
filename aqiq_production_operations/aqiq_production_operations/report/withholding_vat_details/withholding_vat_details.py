# Copyright (c) 2024, RONOH and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, formatdate

def execute(filters=None):
    columns, data = [], []

    # Define columns for the report
    columns = [
        {"label": "PIN of Withholdee", "fieldname": "tax_id", "fieldtype": "Data", "width": 150},
        {"label": "Invoice Number", "fieldname": "name", "fieldtype": "Link", "options": "Purchase Invoice", "width": 150},
        {"label": "Invoice Date", "fieldname": "posting_date", "fieldtype": "Date", "width": 120},
        {"label": "Invoice Amount (Exclusive of VAT)(Ksh)", "fieldname": "base_net_total", "fieldtype": "Currency", "width": 180},
        {"label": "Payment Date to Supplier/Withholdee", "fieldname": "payment_date", "fieldtype": "Date", "width": 180},
        {"label": "Withholding VAT Rate (%)", "fieldname": "withholding_vat_rate", "fieldtype": "Percent", "width": 150},
        {"label": "Withholding VAT Amount (Ksh)", "fieldname": "withholding_vat_amount", "fieldtype": "Currency", "width": 180},
    ]

    # Query Purchase Invoices
    purchase_invoices = frappe.db.sql("""
        SELECT 
            pi.tax_id, pi.name, pi.posting_date, pi.base_net_total,
            pi.base_grand_total, pi.supplier, pi.payment_schedule,
            pii.custom_withholding_vat_percentage AS withholding_vat_rate,
            pii.custom_withholding_vat_amount AS withholding_vat_amount,
            (SELECT MIN(due_date) FROM `tabPayment Schedule` ps WHERE ps.parent = pi.name) AS payment_date
        FROM `tabPurchase Invoice` pi
        LEFT JOIN `tabPurchase Invoice Item` pii ON pii.parent = pi.name
        WHERE pi.docstatus = 1
    """, as_dict=1)

    # Iterate through the result set and format data for the report
    for invoice in purchase_invoices:
        data.append({
            "tax_id": invoice.tax_id,
            "name": invoice.name,
            "posting_date": formatdate(invoice.posting_date),
            "base_net_total": flt(invoice.base_net_total),
            "payment_date": formatdate(invoice.payment_date) if invoice.payment_date else "N/A",
            "withholding_vat_rate": flt(invoice.withholding_vat_rate),
            "withholding_vat_amount": flt(invoice.withholding_vat_amount),
        })

    return columns, data
