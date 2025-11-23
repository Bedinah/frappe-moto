# import frappe
# from frappe.model.document import Document
# from frappe.utils import flt

# class Payment(Document):
#     def validate(self):
#         if flt(self.amount) <= 0:
#             frappe.throw("Payment amount must be greater than 0")

#     def on_submit(self):
#         self.link_to_installment()
#         self.update_contract_balance()

#     def link_to_installment(self):
#         contract = frappe.get_doc("Contract", self.contract)
#         for row in contract.installments:
#             if row.status in ["Pending", "Overdue"] and not row.payment:
#                 row.payment = self.name
#                 row.status = "Paid"
#                 break
#         contract.save(ignore_permissions=True)

#     def update_contract_balance(self):
#         contract = frappe.get_doc("Contract", self.contract)
#         contract.compute_remaining_balance()
#         contract.save(ignore_permissions=True)
#         if flt(contract.remaining_balance) <= 0:
#             contract.status = "Completed"
#             contract.save(ignore_permissions=True)
#             if contract.motorcycle:
#                 frappe.db.set_value("Motorcycle", contract.motorcycle, "status", "Sold")
import frappe
from frappe.model.document import Document
from frappe.utils import flt

class Payment(Document):
    def validate(self):
        # Validate amount
        if flt(self.amount) <= 0:
            frappe.throw("Payment amount must be greater than 0")
        
        # Check contract exists
        if not frappe.db.exists("Contract", self.contract):
            frappe.throw(f"Contract {self.contract} does not exist")

    def on_submit(self):
        # Link payment to installment and update contract
        self.link_to_installment()
        self.update_contract_balance()
        
        # Send notifications
        self.notify_payment_received()

    def link_to_installment(self):
        """Link payment to the earliest unpaid installment"""
        contract = frappe.get_doc("Contract", self.contract)
        payment_amount = flt(self.amount)
        
        for idx, row in enumerate(contract.installments):
            if row.status in ["Pending", "Overdue"] and not row.payment:
                row.payment = self.name
                row.status = "Paid"
                
                # If payment covers this installment, break
                if payment_amount >= flt(row.amount):
                    payment_amount -= flt(row.amount)
                    break
                else:
                    # Partial payment - keep status as pending but note payment
                    break
        
        contract.save(ignore_permissions=True)

    def update_contract_balance(self):
        """Recalculate contract remaining balance"""
        contract = frappe.get_doc("Contract", self.contract)
        contract.compute_remaining_balance()
        contract.save(ignore_permissions=True)
        
        # Check if contract is completed
        if flt(contract.remaining_balance) <= 0:
            contract.status = "Completed"
            contract.save(ignore_permissions=True)
            
            # Update motorcycle status
            if contract.motorcycle:
                frappe.db.set_value("Motorcycle", contract.motorcycle, "status", "Sold")

    def notify_payment_received(self):
        """Send notification to admin about payment"""
        try:
            # Get admin users
            admins = frappe.get_all("User", 
                filters={"enabled": 1, "name": ["!=", "Guest"]},
                fields=["email"])
            
            admin_emails = [u.email for u in admins if u.email]
            
            if admin_emails:
                frappe.sendmail(
                    recipients=admin_emails,
                    subject=f"Payment Received - {self.contract}",
                    message=f"""
                        <h3>Payment Received</h3>
                        <p><strong>Contract:</strong> {self.contract}</p>
                        <p><strong>Amount:</strong> {frappe.format_value(self.amount, 'Currency')}</p>
                        <p><strong>Date:</strong> {self.payment_date}</p>
                        <p><strong>Mode:</strong> {self.mode}</p>
                        <p><strong>Reference:</strong> {self.reference or 'N/A'}</p>
                    """,
                    delayed=False
                )
        except Exception as e:
            frappe.log_error(f"Failed to send payment notification: {str(e)}")