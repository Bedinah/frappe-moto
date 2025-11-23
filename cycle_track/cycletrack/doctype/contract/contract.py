import frappe
from frappe.model.document import Document
from frappe.utils import add_months, getdate

class Contract(Document):
    def validate(self):
        # compute end_date
        if self.start_date and self.duration_months:
            self.end_date = add_months(getdate(self.start_date), self.duration_months)

        # compute remaining_balance
        total_due = (self.total_price or 0) - (self.deposit or 0)
        paid = sum([p.amount for p in frappe.get_all("Payment",
                                                     filters={"contract": self.name},
                                                     fields=["amount"])]) if self.name else 0
        self.remaining_balance = total_due - paid

    def on_submit(self):
        # set motorcycle status to Active Contract
        if self.motorcycle:
            mc = frappe.get_doc("Motorcycle", self.motorcycle)
            mc.status = "Active Contract"
            mc.save()

        # generate installments if none
        if not self.installments:
            self.generate_installments()

        # mark status Active
        self.status = "Active"

    def generate_installments(self):
        self.installments = []
        total_due = (self.total_price or 0) - (self.deposit or 0)
        months = int(self.duration_months or 0)
        monthly = self.monthly_amount or 0

        if months <= 0 or monthly <= 0:
            frappe.throw("Duration and Monthly Amount must be > 0")

        # Optional: adjust last installment for rounding
        remaining = total_due
        for i in range(months):
            due = add_months(getdate(self.start_date), i)
            amount = monthly if remaining >= monthly else remaining
            self.append("installments", {
                "due_date": due,
                "amount": amount,
                "status": "Pending"
            })
            remaining -= amount

        if remaining > 0:
            # if underfunded schedule
            last = self.installments[-1]
            last.amount += remaining

    def check_overdues(self):
        # utility to set overdue status
        for row in self.installments:
            if row.status == "Pending" and getdate(row.due_date) < getdate():
                row.status = "Overdue"
        self.save()

    def after_insert(self):
        # ensure installments exist once created via API (before submit)
        if not self.installments and self.start_date and self.duration_months and self.monthly_amount:
            self.generate_installments()
            self.save()
