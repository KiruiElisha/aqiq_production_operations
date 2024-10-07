import frappe
import qrcode
from io import BytesIO
import base64
from frappe.utils import now_datetime

@frappe.whitelist()
def generate_dispatch_qr_code(delivery_note):
    # Generate a unique URL for the QR code
    url = f"{frappe.utils.get_url()}/api/method/aqiq_production_operations.aqiq_production_operations.rest.update_delivery_note.update_dispatch_status?delivery_note={delivery_note}"
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert image to base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # Create a file in Frappe and return the file URL
    file_doc = frappe.get_doc({
        "doctype": "File",
        "file_name": f"qr_code_{delivery_note}.png",
        "is_private": 0,
        "content": img_str,
        "attached_to_doctype": "Delivery Note",
        "attached_to_name": delivery_note
    })
    file_doc.insert()
    
    return file_doc.file_url  # Return the file URL

@frappe.whitelist()
def update_dispatch_status(delivery_note):
    doc = frappe.get_doc("Delivery Note", delivery_note)
    
    if doc.status == "Dispatched":
        return {"message": "Delivery Note is already dispatched.", "success": False}
    
    doc.status = "Dispatched"
    doc.dispatch_date = now_datetime()
    doc.save()
    frappe.db.commit()
    
    return {"message": "Delivery Note status updated to Dispatched.", "success": True}
