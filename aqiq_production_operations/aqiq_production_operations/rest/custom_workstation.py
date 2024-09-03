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
from frappe.utils.pdf import get_pdf
from urllib.parse import quote
import json

@frappe.whitelist()
def custom_print_qr_codes(workstations):
    # Parse the JSON string if it's provided as a string
    if isinstance(workstations, str):
        try:
            workstations = json.loads(workstations)
        except json.JSONDecodeError:
            frappe.throw("Invalid JSON format for workstations.")
    
    # Ensure that workstations is a list of dictionaries
    if not isinstance(workstations, list) or not all(isinstance(ws, dict) for ws in workstations):
        frappe.throw("Workstations should be a list of dictionaries.")

    # Generate the HTML content
    html = '''
    <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                }
                .qr-code-container {
                    margin: 20px;
                    padding: 10px;
                    background-color: #f8f8f8;
                    border-radius: 8px;
                    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                }
                .qr-code-title {
                    font-size: 18px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 10px;
                }
                .qr-code-image {
                    max-width: 200px;
                    max-height: 200px;
                }
                .qr-code {
                    margin-bottom: 40px; /* Adjust spacing between QR codes */
                }
            </style>
        </head>
        <body>
    '''
    
    for workstation in workstations:
        # Handle cases where 'qr_code' might be missing
        qr_code = workstation.get('qr_code', 'No QR Code Available')
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?data={quote(qr_code)}&size=200x200"
        html += f'''
        <div class="qr-code">
            <div class="qr-code-container">
                <div class="qr-code-title">{workstation.get('name', 'Unnamed Workstation')}</div>
                <img src="{qr_code_url}" alt="QR Code" class="qr-code-image" />
            </div>
        </div>
        '''
    
    html += '''
        </body>
    </html>
    '''
    
    # Convert HTML to PDF
    pdf = get_pdf(html)
    
    # Save the PDF and return the URL
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": "Workstation_QR_Codes.pdf",
        "is_private": 0,
        "content": pdf,
        "decode": False
    })
    file_doc.save()
    
    return file_doc.file_url


