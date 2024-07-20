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