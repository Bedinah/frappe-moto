import frappe

def get_context(context):
    # Find the customer profile linked to the logged-in user
    user = frappe.session.user
    prof = frappe.db.get_value("Customer Profile", {"user": user}, "name")
    contracts = []
    if prof:
        contracts = frappe.get_all(
            "Contract",
            filters={"customer": prof},
            fields=["name", "status", "remaining_balance", "start_date", "end_date"]
        )
    context.contracts = contracts
    return context
