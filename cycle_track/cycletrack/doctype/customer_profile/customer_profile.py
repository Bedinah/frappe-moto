import frappe
from frappe.model.document import Document

class CustomerProfile(Document):
    def validate(self):
        if self.user:
            user = frappe.get_doc("User", self.user)
            if "Customer" not in [r.role for r in user.roles]:
                user.add_roles("Customer")