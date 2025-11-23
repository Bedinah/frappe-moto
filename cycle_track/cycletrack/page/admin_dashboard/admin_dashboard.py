import frappe
from frappe.utils import getdate

@frappe.whitelist()
def get_admin_kpis():
    total_motorcycles = frappe.db.count("Motorcycle")
    active_contracts = frappe.db.count("Contract", {"status": "Active"})

    # money received this month
    payments = frappe.get_all("Payment",
        filters={"payment_date": [">=", getdate().replace(day=1)]},
        fields=["amount"])
    money_this_month = sum([p.amount for p in payments])

    # outstanding balances
    contracts = frappe.get_all("Contract", fields=["name", "remaining_balance"])
    outstanding = sum([c.remaining_balance or 0 for c in contracts])

    # late customers
    late = 0
    for c in frappe.get_all("Contract", filters={"status": "Active"}, fields=["name"]):
        doc = frappe.get_doc("Contract", c.name)
        if any([row.status == "Overdue" for row in doc.installments]):
            late += 1

    return {
        "total_motorcycles": total_motorcycles,
        "active_contracts": active_contracts,
        "money_this_month": money_this_month,
        "outstanding": outstanding,
        "late_customers": late
    }

