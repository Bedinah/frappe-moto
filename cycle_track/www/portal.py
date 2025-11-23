import frappe
from frappe.utils import flt

def _get_customer_contracts(user):
    prof = frappe.db.get_value("Customer Profile", {"user": user}, "name")
    if not prof:
        return []
    return frappe.get_all("Contract",
        filters={"customer": prof},
        fields=["name", "remaining_balance", "status", "start_date", "end_date"])

def get_context(context):
    return context
def get_customer_kpis(user):
    contracts = _get_customer_contracts(user)
    total_contracts = len(contracts)
    active_contracts = len([c for c in contracts if c.status == "Active"])
    outstanding_balance = sum([flt(c.remaining_balance or 0) for c in contracts])

    return {
        "total_contracts": total_contracts,
        "active_contracts": active_contracts,
        "outstanding_balance": outstanding_balance
    }