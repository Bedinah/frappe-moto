import frappe
from frappe.model.document import Document

class Motorcycle(Document):
    def validate(self):
        if self.status not in ["Available", "Active Contract", "Completed", "Sold"]:
            frappe.throw("Invalid status")