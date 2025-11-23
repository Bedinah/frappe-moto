import frappe
def execute():
    if not frappe.db.exists("Motorcycle", {"plate_number": "RWA-001"}):
        frappe.get_doc({"doctype":"Motorcycle","brand":"Bajaj","model":"Boxer","year":2022,"plate_number":"RWA-001","price":1200000}).insert()
