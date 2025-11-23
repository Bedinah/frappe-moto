import frappe
from frappe.utils import getdate, flt, add_days, nowdate
from frappe import _

# ============================================================================
# CUSTOMER ENDPOINTS
# ============================================================================

@frappe.whitelist()
def get_customer_profile():
    """Get current logged-in customer's profile and active contract"""
    user = frappe.session.user
    
    if user == "Guest":
        return {"error": "Not authenticated", "data": None}
    
    # Find customer profile linked to user
    profile = frappe.db.get_value("Customer Profile", {"user": user}, "name")
    if not profile:
        return {"error": "No customer profile found", "data": None}
    
    # Get customer details
    customer_doc = frappe.get_doc("Customer Profile", profile)
    
    # Get all contracts
    contracts = frappe.get_all("Contract",
        filters={"customer": profile, "docstatus": 1},
        fields=["name", "status", "remaining_balance", "total_price", 
                "deposit", "start_date", "end_date", "motorcycle"])
    
    # Get active contract with details
    active_contract = None
    for c in contracts:
        if c.status == "Active":
            contract_doc = frappe.get_doc("Contract", c.name)
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
        "success": True,
        "data": {
            "profile": {
                "name": customer_doc.name,
                "full_name": customer_doc.full_name,
                "phone": customer_doc.phone,
                "email": customer_doc.email,
                "status": customer_doc.status
            },
            "contracts": contracts,
            "active_contract": active_contract
        }
    }


@frappe.whitelist()
def get_contract_details(contract_name):
    """Get detailed contract information with installments"""
    user = frappe.session.user
    
    contract = frappe.get_doc("Contract", contract_name)
    
    # Check permissions
    if user != "Administrator":
        profile = frappe.db.get_value("Customer Profile", {"user": user}, "name")
        if contract.customer != profile:
            return {"error": "You don't have permission to view this contract", "data": None}
    
    motorcycle = frappe.get_doc("Motorcycle", contract.motorcycle) if contract.motorcycle else None
    
    installments = []
    for inst in contract.installments:
        installments.append({
            "due_date": inst.due_date,
            "amount": inst.amount,
            "status": inst.status,
            "payment": inst.payment
        })
    
    return {
        "success": True,
        "data": {
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
    }


@frappe.whitelist()
def list_payments():
    """Get payment history for current customer"""
    user = frappe.session.user
    
    profile = frappe.db.get_value("Customer Profile", {"user": user}, "name")
    if not profile:
        return {"error": "No customer profile found", "data": []}
    
    # Get contracts for this customer
    contracts = frappe.get_all("Contract",
        filters={"customer": profile},
        fields=["name"])
    
    contract_names = [c.name for c in contracts]
    
    if not contract_names:
        return {"success": True, "data": []}
    
    # Get payments
    payments = frappe.get_all("Payment",
        filters={"contract": ["in", contract_names], "docstatus": 1},
        fields=["name", "contract", "amount", "payment_date", "mode", "reference"],
        order_by="payment_date desc",
        limit=50)
    
    return {"success": True, "data": payments}


@frappe.whitelist()
def list_installments():
    """Get all installments for customer's contracts"""
    user = frappe.session.user
    
    profile = frappe.db.get_value("Customer Profile", {"user": user}, "name")
    if not profile:
        return {"error": "No customer profile found", "data": []}
    
    contracts = frappe.get_all("Contract",
        filters={"customer": profile, "docstatus": 1},
        fields=["name"])
    
    all_installments = []
    for c in contracts:
        contract_doc = frappe.get_doc("Contract", c.name)
        for idx, inst in enumerate(contract_doc.installments):
            all_installments.append({
                "contract": c.name,
                "row": idx + 1,
                "due_date": inst.due_date,
                "amount": inst.amount,
                "status": inst.status,
                "payment": inst.payment
            })
    
    return {"success": True, "data": all_installments}


@frappe.whitelist()
def pay_installment(contract, amount, payment_date, mode, reference=None):
    """Record a payment for an installment"""
    user = frappe.session.user
    
    # Verify customer owns this contract
    profile = frappe.db.get_value("Customer Profile", {"user": user}, "name")
    contract_doc = frappe.get_doc("Contract", contract)
    
    if contract_doc.customer != profile and user != "Administrator":
        return {"success": False, "error": "You don't have permission to pay this contract"}
    
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
            "error": str(e)
        }


# ============================================================================
# ADMIN ENDPOINTS
# ============================================================================

@frappe.whitelist()
def get_admin_dashboard():
    """Get admin dashboard KPIs and overview"""
    
    # Total motorcycles
    total_motorcycles = frappe.db.count("Motorcycle")
    available_motorcycles = frappe.db.count("Motorcycle", {"status": "Available"})
    
    # Active contracts
    active_contracts = frappe.db.count("Contract", {"status": "Active", "docstatus": 1})
    completed_contracts = frappe.db.count("Contract", {"status": "Completed", "docstatus": 1})
    
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
    
    # Late customers
    late_customers = 0
    active_contracts_list = frappe.get_all("Contract", 
        filters={"status": "Active", "docstatus": 1}, 
        fields=["name"])
    
    for c in active_contracts_list:
        doc = frappe.get_doc("Contract", c.name)
        if any([row.status == "Overdue" for row in doc.installments]):
            late_customers += 1
    
    return {
        "success": True,
        "data": {
            "total_motorcycles": total_motorcycles,
            "available_motorcycles": available_motorcycles,
            "active_contracts": active_contracts,
            "completed_contracts": completed_contracts,
            "money_this_month": money_this_month,
            "outstanding": outstanding,
            "late_customers": late_customers
        }
    }


@frappe.whitelist()
def list_contracts(status=None, limit=50):
    """List all contracts (admin only)"""
    filters = {"docstatus": 1}
    if status:
        filters["status"] = status
    
    contracts = frappe.get_all("Contract",
        filters=filters,
        fields=["name", "customer", "motorcycle", "status", "total_price", 
                "remaining_balance", "start_date", "end_date"],
        order_by="creation desc",
        limit=limit)
    
    # Enrich with customer and motorcycle names
    enriched = []
    for c in contracts:
        customer_doc = frappe.get_doc("Customer Profile", c.customer)
        motorcycle_doc = frappe.get_doc("Motorcycle", c.motorcycle) if c.motorcycle else None
        
        enriched.append({
            "name": c.name,
            "customer": c.customer,
            "customer_name": customer_doc.full_name,
            "motorcycle": c.motorcycle,
            "motorcycle_name": f"{motorcycle_doc.brand} {motorcycle_doc.model}" if motorcycle_doc else "N/A",
            "status": c.status,
            "total_price": c.total_price,
            "remaining_balance": c.remaining_balance,
            "start_date": c.start_date,
            "end_date": c.end_date
        })
    
    return {"success": True, "data": enriched}


@frappe.whitelist()
def get_admin_payments(limit=20):
    """Get recent payments for admin dashboard"""
    payments = frappe.get_all("Payment",
        filters={"docstatus": 1},
        fields=["name", "contract", "amount", "payment_date", "mode", "reference"],
        order_by="payment_date desc",
        limit=limit)
    
    return {"success": True, "data": payments}


@frappe.whitelist()
def get_available_motorcycles():
    """Get list of available motorcycles for new contracts"""
    motorcycles = frappe.get_all("Motorcycle",
        filters={"status": "Available"},
        fields=["name", "brand", "model", "year", "plate_number", "price"])
    
    return {"success": True, "data": motorcycles}


@frappe.whitelist()
def create_contract(customer, motorcycle, total_price, deposit, duration_months, 
                   monthly_amount, start_date):
    """Create a new contract (admin only)"""
    try:
        contract = frappe.get_doc({
            "doctype": "Contract",
            "customer": customer,
            "motorcycle": motorcycle,
            "total_price": flt(total_price),
            "deposit": flt(deposit),
            "duration_months": int(duration_months),
            "monthly_amount": flt(monthly_amount),
            "start_date": start_date,
            "status": "Draft"
        })
        contract.insert()
        contract.submit()
        
        return {
            "success": True,
            "message": "Contract created and submitted successfully",
            "contract_name": contract.name
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Contract Creation Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def list_customers(limit=50):
    """List all customers"""
    customers = frappe.get_all("Customer Profile",
        fields=["name", "full_name", "phone", "email", "status"],
        order_by="creation desc",
        limit=limit)
    
    # Add contract count
    enriched = []
    for c in customers:
        contract_count = frappe.db.count("Contract", {"customer": c.name})
        enriched.append({
            **c,
            "contract_count": contract_count
        })
    
    return {"success": True, "data": enriched}


@frappe.whitelist()
def create_customer(full_name, phone, email, user=None):
    """Create a new customer profile"""
    try:
        customer = frappe.get_doc({
            "doctype": "Customer Profile",
            "full_name": full_name,
            "phone": phone,
            "email": email,
            "user": user,
            "status": "Active"
        })
        customer.insert()
        
        return {
            "success": True,
            "message": "Customer created successfully",
            "customer_name": customer.name
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Customer Creation Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def update_customer(customer_name, full_name, phone, email, status):
    """Update customer profile"""
    try:
        customer = frappe.get_doc("Customer Profile", customer_name)
        customer.full_name = full_name
        customer.phone = phone
        customer.email = email
        customer.status = status
        customer.save()
        
        return {
            "success": True,
            "message": "Customer updated successfully"
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Customer Update Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def create_motorcycle(brand, model, year, plate_number, price):
    """Create a new motorcycle"""
    try:
        motorcycle = frappe.get_doc({
            "doctype": "Motorcycle",
            "brand": brand,
            "model": model,
            "year": int(year),
            "plate_number": plate_number,
            "price": flt(price),
            "status": "Available"
        })
        motorcycle.insert()
        
        return {
            "success": True,
            "message": "Motorcycle created successfully",
            "motorcycle_name": motorcycle.name
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Motorcycle Creation Error")
        return {
            "success": False,
            "error": str(e)
        }


@frappe.whitelist()
def list_motorcycles(limit=100):
    """List all motorcycles"""
    motorcycles = frappe.get_all("Motorcycle",
        fields=["name", "brand", "model", "year", "plate_number", "price", "status"],
        order_by="creation desc",
        limit=limit)
    
    return {"success": True, "data": motorcycles}


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
    
    return {"success": True, "message": f"Checked {updated} contracts for overdue payments"}