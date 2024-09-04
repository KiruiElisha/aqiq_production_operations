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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor
from reportlab.platypus import Frame, PageTemplate, FrameBreak

@frappe.whitelist()
def custom_print_qr_codes(workstations):
    workstations = frappe.parse_json(workstations)
    
    # Prepare the PDF
    file_name = f"Workstation_QR_Codes_{frappe.utils.now()}.pdf"
    file_path = os.path.join(get_files_path(), file_name)
    doc = SimpleDocTemplate(file_path, pagesize=A4)

    # Prepare styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], alignment=1, spaceAfter=1*cm, textColor=HexColor("#1a237e"))
    name_style = ParagraphStyle('Name', parent=styles['Normal'], alignment=1, fontSize=14, textColor=HexColor("#303f9f"))

    # Create a frame for centered content
    frame_width = A4[0] - 4*cm
    frame_height = A4[1] - 4*cm
    frame = Frame(2*cm, 2*cm, frame_width, frame_height, id='centered_frame')

    # Create a PageTemplate with the centered frame
    template = PageTemplate(id='centered_template', frames=[frame])
    doc.addPageTemplates([template])

    # Prepare content
    content = []
    content.append(Paragraph("Workstation QR Codes", title_style))

    for workstation in workstations:
        # Fetch the workstation document to get the custom_workstation_qr_code
        workstation_doc = frappe.get_doc("Workstation", workstation['name'])
        qr_code_data = workstation_doc.custom_workstation_qr_code

        if not qr_code_data:
            frappe.msgprint(f"No QR code data found for workstation {workstation['name']}")
            continue

        # Create QR code
        qr_code = QrCodeWidget(qr_code_data)
        qr_code.barWidth = 5*cm
        qr_code.barHeight = 5*cm
        d = Drawing(5*cm, 5*cm)
        d.add(qr_code)
        
        # Center the QR code with the accompanying text
        content.append(Spacer(1, 1*cm))
        content.append(Paragraph(f"WS: {workstation['name']}", name_style))
        content.append(Spacer(1, 0.5*cm))
        content.append(d)
        content.append(Spacer(1, 2*cm))  # Add more space between QR codes

    if not content[1:]:
        frappe.throw("No valid QR code data found for any selected workstations")

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




