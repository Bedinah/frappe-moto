import frappe
from frappe.model.document import Document
from frappe.utils import add_months, getdate, flt, nowdate

class Contract(Document):
    def validate(self):
        # Compute end_date
        if self.start_date and self.duration_months:
            self.end_date = add_months(getdate(self.start_date), int(self.duration_months))

        # Validate monthly amount
        total_due = flt(self.total_price) - flt(self.deposit)
        if self.monthly_amount and self.duration_months:
            expected_total = flt(self.monthly_amount) * int(self.duration_months)
            if abs(expected_total - total_due) > 100:
                frappe.msgprint(f"Warning: Monthly payments ({expected_total}) don't match total due ({total_due})")

        # Compute remaining balance
        self.compute_remaining_balance()

    def compute_remaining_balance(self):
        total_due = flt(self.total_price) - flt(self.deposit)
        paid = flt(frappe.db.sql("""
            SELECT SUM(amount) 
            FROM `tabPayment` 
            WHERE contract = %s AND docstatus = 1
        """, self.name)[0][0] or 0)
        self.remaining_balance = total_due - paid

    def on_submit(self):
        # Set motorcycle status
        if self.motorcycle:
            frappe.db.set_value("Motorcycle", self.motorcycle, "status", "Active Contract")

        # Generate installments if none exist
        if not self.installments:
            self.generate_installments()
            self.save()

        # Set contract status to Active
        self.status = "Active"
        self.db_update()

    def generate_installments(self):
        """Generate monthly installment schedule"""
        if not self.start_date or not self.duration_months or not self.monthly_amount:
            frappe.throw("Please provide Start Date, Duration, and Monthly Amount")

        self.installments = []
        total_due = flt(self.total_price) - flt(self.deposit)
        monthly = flt(self.monthly_amount)
        months = int(self.duration_months)
        
        remaining = total_due
        
        for i in range(months):
            due_date = add_months(getdate(self.start_date), i)
            
            # Last installment gets any remaining amount
            if i == months - 1:
                amount = remaining
            else:
                amount = monthly
            
            self.append("installments", {
                "due_date": due_date,
                "amount": amount,
                "status": "Pending"
            })
            
            remaining -= amount

    def check_overdue_installments(self):
        """Mark installments as overdue if past due date"""
        today = getdate(nowdate())
        updated = False
        
        for row in self.installments:
            if row.status == "Pending" and getdate(row.due_date) < today:
                row.status = "Overdue"
                updated = True
        
        if updated:
            self.save()
            
    def get_next_due_installment(self):
        """Get the next unpaid installment"""
        for row in self.installments:
            if row.status in ["Pending", "Overdue"]:
                return row
        return None

    def on_cancel(self):
        # Reset motorcycle status
        if self.motorcycle:
            frappe.db.set_value("Motorcycle", self.motorcycle, "status", "Available")