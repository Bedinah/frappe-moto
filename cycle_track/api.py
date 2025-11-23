import frappe
from frappe.utils import getdate, flt, add_days
from frappe import _

@frappe.whitelist()
def get_admin_dashboard():
    """Get admin dashboard KPIs"""
    
    # Total motorcycles
    total_motorcycles = frappe.db.count("Motorcycle")
    available_motorcycles = frappe.db.count("Motorcycle", {"status": "Available"})
    
    # Active contracts
    active_contracts = frappe.db.count("Contract", {"status": "Active", "docstatus": 1})
    
    # Money received this month
    first_day = getdate().replace(day=1)
    payments = frappe.get_all("Payment",
        filters={
            "payment_date": [">=", first_day],
            "docstatus": 1
        },
        fields=["amount"])
    money_this_month = sum([flt(p.amount) for p in payments])
    
    # Outstanding balances
    contracts = frappe.get_all("Contract", 
        filters={"status": "Active", "docstatus": 1},
        fields=["remaining_balance"])
    outstanding = sum([flt(c.remaining_balance) for c in contracts])
    
    # Late customers (contracts with overdue installments)
    late_customers = 0
    active_contracts_list = frappe.get_all("Contract", 
        filters={"status": "Active", "docstatus": 1}, 
        fields=["name"])
    
    for c in active_contracts_list:
        doc = frappe.get_doc("Contract", c.name)
        if any([row.status == "Overdue" for row in doc.installments]):
            late_customers += 1
    
    # Recent payments
    recent_payments = frappe.get_all("Payment",
        filters={"docstatus": 1},
        fields=["name", "contract", "amount", "payment_date", "mode"],
        order_by="payment_date desc",
        limit=10)
    
    return {
        "total_motorcycles": total_motorcycles,
        "available_motorcycles": available_motorcycles,
        "active_contracts": active_contracts,
        "money_this_month": money_this_month,
        "outstanding": outstanding,
        "late_customers": late_customers,
        "recent_payments": recent_payments
    }

@frappe.whitelist()
def get_customer_dashboard():
    """Get customer dashboard data"""
    user = frappe.session.user
    
    # Find customer profile
    profile = frappe.db.get_value("Customer Profile", {"user": user}, "name")
    if not profile:
        return {"error": "No customer profile found", "contracts": [], "active_contract": None}
    
    # Get contracts
    contracts = frappe.get_all("Contract",
        filters={"customer": profile, "docstatus": 1},
        fields=["name", "status", "remaining_balance", "total_price", 
                "deposit", "start_date", "end_date", "motorcycle"])
    
    if not contracts:
        return {"contracts": [], "active_contract": None}
    
    # Get active contract details
    active_contract = None
    for c in contracts:
        if c.status == "Active":
            contract_doc = frappe.get_doc("Contract", c.name)
            
            # Get next due installment
            next_due = None
            overdue_count = 0
            total_paid = 0
            
            for inst in contract_doc.installments:
                if inst.status == "Paid":
                    total_paid += flt(inst.amount)
                elif inst.status in ["Pending", "Overdue"]:
                    if not next_due:
                        next_due = {
                            "date": inst.due_date,
                            "amount": inst.amount,
                            "status": inst.status
                        }
                if inst.status == "Overdue":
                    overdue_count += 1
            
            # Get motorcycle details
            motorcycle = frappe.get_doc("Motorcycle", c.motorcycle) if c.motorcycle else None
            
            active_contract = {
                "name": c.name,
                "status": c.status,
                "remaining_balance": c.remaining_balance,
                "total_price": c.total_price,
                "total_paid": total_paid,
                "deposit": c.deposit,
                "start_date": c.start_date,
                "end_date": c.end_date,
                "next_due": next_due,
                "overdue_count": overdue_count,
                "motorcycle": {
                    "brand": motorcycle.brand,
                    "model": motorcycle.model,
                    "year": motorcycle.year,
                    "plate_number": motorcycle.plate_number
                } if motorcycle else None
            }
            break
    
    return {
        "contracts": contracts,
        "active_contract": active_contract
    }

@frappe.whitelist()
def get_contract_details(contract_name):
    """Get detailed contract information with installments"""
    contract = frappe.get_doc("Contract", contract_name)
    
    # Check permissions
    user = frappe.session.user
    if user != "Administrator":
        profile = frappe.db.get_value("Customer Profile", {"user": user}, "name")
        if contract.customer != profile:
            frappe.throw("You don't have permission to view this contract")
    
    # Get motorcycle details
    motorcycle = frappe.get_doc("Motorcycle", contract.motorcycle) if contract.motorcycle else None
    
    # Format installments
    installments = []
    for inst in contract.installments:
        installments.append({
            "due_date": inst.due_date,
            "amount": inst.amount,
            "status": inst.status,
            "payment": inst.payment
        })
    
    return {
        "contract": {
            "name": contract.name,
            "status": contract.status,
            "total_price": contract.total_price,
            "deposit": contract.deposit,
            "remaining_balance": contract.remaining_balance,
            "duration_months": contract.duration_months,
            "monthly_amount": contract.monthly_amount,
            "start_date": contract.start_date,
            "end_date": contract.end_date
        },
        "motorcycle": {
            "brand": motorcycle.brand,
            "model": motorcycle.model,
            "year": motorcycle.year,
            "plate_number": motorcycle.plate_number,
            "price": motorcycle.price
        } if motorcycle else None,
        "installments": installments
    }

@frappe.whitelist()
def create_payment(contract, amount, payment_date, mode, reference=None):
    """Create a new payment"""
    try:
        payment = frappe.get_doc({
            "doctype": "Payment",
            "contract": contract,
            "amount": flt(amount),
            "payment_date": payment_date,
            "mode": mode,
            "reference": reference
        })
        payment.insert()
        payment.submit()
        
        return {
            "success": True,
            "message": "Payment recorded successfully",
            "payment_name": payment.name
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Payment Creation Error")
        return {
            "success": False,
            "message": str(e)
        }

@frappe.whitelist()
def get_available_motorcycles():
    """Get list of available motorcycles for new contracts"""
    motorcycles = frappe.get_all("Motorcycle",
        filters={"status": "Available"},
        fields=["name", "brand", "model", "year", "plate_number", "price"])
    
    return motorcycles

@frappe.whitelist()
def check_overdue_payments():
    """Check and update overdue installments for all active contracts"""
    active_contracts = frappe.get_all("Contract", 
        filters={"status": "Active", "docstatus": 1})
    
    updated = 0
    for c in active_contracts:
        doc = frappe.get_doc("Contract", c.name)
        doc.check_overdue_installments()
        updated += 1
    
    return {"message": f"Checked {updated} contracts for overdue payments"}