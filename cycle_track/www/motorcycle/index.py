import frappe

def get_context(context):
    # Find the customer profile linked to the logged-in user
    user = frappe.session.user
    prof = frappe.db.get_value("Customer Profile", {"user": user}, "name")
    motos = []
    if prof:
        motos = frappe.get_all(
            "motos",
            filters={"customer": prof},
            fields=["name", "status", "remaining_balance", "start_date", "end_date"]
        )
    context.motos = motos
    return context
