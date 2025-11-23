import frappe

def get_context(context):
    if frappe.form_dict and frappe.request.method == "POST":
        amount = float(frappe.form_dict.amount)
        payment_date = frappe.form_dict.payment_date
        mode = frappe.form_dict.mode
        reference = frappe.form_dict.reference
        contract = frappe.form_dict.contract

        p = frappe.get_doc({
            "doctype": "Payment",
            "contract": contract,
            "amount": amount,
            "payment_date": payment_date,
            "mode": mode,
            "reference": reference
        })
        p.insert()
        p.submit()
        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = f"/payments?contract={contract}"
    return context
