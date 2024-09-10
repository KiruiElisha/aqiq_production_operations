import json
import base64
import frappe
from frappe.model.document import Document

def encode_workstation_data(workstation):
    # Ensure the workstation has a password
    if not workstation.custom_workstation_password:
        frappe.throw("Workstation password is not set")
    
    # Create a dictionary with workstation name and password
    data = {
        "workstation": workstation.name,
        "password": workstation.custom_workstation_password
    }
    
    # Convert the dictionary to a JSON string
    json_data = json.dumps(data)
    
    # Encode the JSON string to base64
    encoded_data = base64.b64encode(json_data.encode()).decode()
    
    # Update the Workstation document with the encoded data
    workstation.custom_workstation_qr_code = encoded_data
    workstation.db_update()

    frappe.db.commit()

class CustomWorkstation(Document):
    def on_update(self):
        if self.docstatus == 1:  # Check if the document is submitted
            encode_workstation_data(self)

def on_workstation_after_submit(doc, method):
    encode_workstation_data(doc)

@frappe.whitelist()
def generate_workstation_qr_code(workstation_name):
    workstation = frappe.get_doc("Workstation", workstation_name)
    encode_workstation_data(workstation)
    return workstation.custom_workstation_qr_code

# You can add this function if you want to manually trigger QR code generation via a custom button
@frappe.whitelist()
def generate_qr_code_button(workstation_name):
    encoded_data = generate_workstation_qr_code(workstation_name)
    frappe.msgprint(f"QR Code generated successfully for {workstation_name}")
    return encoded_data

import frappe
from frappe import _
from frappe.utils import get_files_path
import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Frame, PageTemplate, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.lib.colors import HexColor

@frappe.whitelist()
def custom_print_qr_codes(workstations, doctype="Workstation", qr_field="custom_workstation_qr_code", title_field="name"):
    workstations = frappe.parse_json(workstations)
    
    # Prepare the PDF
    file_name = f"{doctype}_QR_Codes_{frappe.utils.now()}.pdf"
    file_path = os.path.join(get_files_path(), file_name)
    doc = SimpleDocTemplate(file_path, pagesize=A4)

    # Prepare styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=0.5*cm)
    name_style = ParagraphStyle('Name', parent=styles['Normal'], alignment=1, fontSize=16, spaceAfter=0.2*cm)

    # Create a frame for centered content
    margin = 2*cm
    frame_width = A4[0] - 2*margin
    frame_height = A4[1] - 2*margin
    frame = Frame(margin, margin, frame_width, frame_height, id='centered_frame')

    # Create a PageTemplate with dynamic header and footer
    def add_page_elements(canvas, doc):
        canvas.saveState()
        
        # Add header
        canvas.setFont("Helvetica-Bold", 14)
        canvas.drawCentredString(A4[0]/2, A4[1]-20*mm, f"{doctype} QR Codes")
        
        # Add footer with page number and timestamp
        canvas.setFont("Helvetica", 9)
        canvas.drawString(10*mm, 10*mm, f"Generated on: {frappe.utils.now_datetime().strftime('%Y-%m-%d %H:%M:%S')}")
        canvas.drawRightString(A4[0]-10*mm, 10*mm, f"Page {doc.page}")
        
        canvas.restoreState()

    template = PageTemplate(id='dynamic_template', frames=[frame], onPage=add_page_elements)
    doc.addPageTemplates([template])

    # Prepare content
    content = [Paragraph(f"{doctype} QR Codes", title_style), Spacer(1, 1*cm)]

    for i, item in enumerate(workstations):
        doc_obj = frappe.get_doc(doctype, item['name'])
        qr_code_data = getattr(doc_obj, qr_field, None)

        if not qr_code_data:
            frappe.msgprint(f"No QR code data found for {doctype} {item['name']}")
            continue

        # Create a KeepTogether block for each workstation
        keep_together = [Paragraph(f"{getattr(doc_obj, title_field)}", name_style)]

        # Create QR code with border
        qr_code = QrCodeWidget(qr_code_data)
        qr_code_size = 7*cm  # Reduced from 10cm to 7cm
        qr_code.barWidth = qr_code_size
        qr_code.barHeight = qr_code_size
        d = Drawing(frame_width, qr_code_size + 0.5*cm)
        d.add(Rect(0, 0, qr_code_size + 0.5*cm, qr_code_size + 0.5*cm, fillColor=None, strokeColor=HexColor("#303f9f"), strokeWidth=1))
        d.add(qr_code)
        d.translate((frame_width - (qr_code_size + 0.5*cm)) / 2, 0.25*cm)
        
        keep_together.append(d)
        
        # Add the KeepTogether block to the content
        content.append(KeepTogether(keep_together))
        
        if i < len(workstations) - 1:
            content.append(Spacer(1, 1.5*cm))  # Reduced spacer from 2cm to 1.5cm

    if not content[2:]:  # Check if any QR codes were added (excluding title and initial spacer)
        frappe.throw(f"No valid QR code data found for any selected {doctype}")

    # Build the PDF
    doc.build(content)

    # Create a File document
    file_url = f"/files/{file_name}"
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": file_name,
        "file_url": file_url,
        "is_private": 0,
        "folder": "Home"
    })
    file_doc.insert(ignore_permissions=True)

    return file_url