import frappe
from frappe.utils import getdate, add_days

def send_monthly_reminders():
    # remind customers 3 days before due date
    contracts = frappe.get_all("Contract", filters={"status": "Active"}, fields=["name", "customer"])
    for c in contracts:
        doc = frappe.get_doc("Contract", c.name)
        for row in doc.installments:
            if row.status in ["Pending", "Overdue"]:
                if getdate(row.due_date) == add_days(getdate(), 3):
                    _notify_customer(doc.customer, c.name, row.due_date, row.amount)

def send_overdue_notices():
    contracts = frappe.get_all("Contract", filters={"status": "Active"}, fields=["name", "customer"])
    for c in contracts:
        doc = frappe.get_doc("Contract", c.name)
        doc.check_overdues()
        for row in doc.installments:
            if row.status == "Overdue":
                _notify_customer(doc.customer, c.name, row.due_date, row.amount, overdue=True)
                _notify_admin_overdue(c.name, row.due_date, row.amount)

def notify_admin_payment(contract, payment):
    _notify_admin_payment(contract, payment)

def _notify_customer(customer_profile, contract_name, due_date, amount, overdue=False):
    cust = frappe.get_doc("Customer Profile", customer_profile)
    subject = "Payment Overdue" if overdue else "Upcoming Payment Reminder"
    message = f"Contract {contract_name}: Amount {amount} due on {due_date}."
    if cust.email:
        frappe.sendmail(recipients=[cust.email], subject=subject, message=message)

def _notify_admin_overdue(contract_name, due_date, amount):
    admins = frappe.get_all("User", filters={"enabled": 1}, fields=["name", "email"])
    emails = [u.email for u in admins if u.email]
    frappe.sendmail(recipients=emails, subject="Overdue Payment",
                    message=f"Contract {contract_name} overdue: {amount} on {due_date}")

def _notify_admin_payment(contract_name, payment_name):
    admins = frappe.get_all("User", filters={"enabled": 1}, fields=["name", "email"])
    emails = [u.email for u in admins if u.email]
    frappe.sendmail(recipients=emails, subject="Payment Received",
                    message=f"Payment {payment_name} received for Contract {contract_name}")

