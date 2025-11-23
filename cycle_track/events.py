import frappe
from frappe.utils import getdate, add_days, nowdate, flt
from frappe import _

# Scheduled Events

def send_payment_reminders():
    """Send payment reminders 3 days before due date"""
    reminder_date = add_days(getdate(nowdate()), 3)
    
    contracts = frappe.get_all("Contract", 
        filters={"status": "Active", "docstatus": 1},
        fields=["name", "customer"])
    
    for contract in contracts:
        doc = frappe.get_doc("Contract", contract.name)
        
        for inst in doc.installments:
            if inst.status in ["Pending"] and getdate(inst.due_date) == reminder_date:
                send_reminder_to_customer(
                    doc.customer,
                    contract.name,
                    inst.due_date,
                    inst.amount
                )

def check_overdue_payments():
    """Check and mark overdue installments daily"""
    contracts = frappe.get_all("Contract",
        filters={"status": "Active", "docstatus": 1})
    
    for c in contracts:
        doc = frappe.get_doc("Contract", c.name)
        doc.check_overdue_installments()

def send_overdue_notices():
    """Send notices for overdue payments"""
    contracts = frappe.get_all("Contract",
        filters={"status": "Active", "docstatus": 1},
        fields=["name", "customer"])
    
    for contract in contracts:
        doc = frappe.get_doc("Contract", contract.name)
        overdue_installments = [i for i in doc.installments if i.status == "Overdue"]
        
        if overdue_installments:
            # Notify customer
            total_overdue = sum([flt(i.amount) for i in overdue_installments])
            send_overdue_notice_to_customer(
                doc.customer,
                contract.name,
                len(overdue_installments),
                total_overdue
            )
            
            # Notify admin
            notify_admin_overdue(
                contract.name,
                doc.customer,
                len(overdue_installments),
                total_overdue
            )

def send_weekly_summary():
    """Send weekly summary to admin"""
    summary = get_weekly_summary()
    send_admin_weekly_report(summary)

# Document Event Handlers

def on_contract_submit(doc, method):
    """Handle contract submission"""
    frappe.logger().info(f"Contract {doc.name} submitted")
    send_contract_confirmation(doc)

def on_contract_cancel(doc, method):
    """Handle contract cancellation"""
    frappe.logger().info(f"Contract {doc.name} cancelled")

def on_payment_submit(doc, method):
    """Handle payment submission"""
    frappe.logger().info(f"Payment {doc.name} submitted")

# Helper Functions

def send_reminder_to_customer(customer_profile, contract_name, due_date, amount):
    """Send payment reminder email to customer"""
    try:
        customer = frappe.get_doc("Customer Profile", customer_profile)
        
        if not customer.email:
            return
        
        subject = f"Payment Reminder - {contract_name}"
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #6366f1;">Payment Reminder</h2>
            <p>Dear {customer.full_name},</p>
            <p>This is a friendly reminder that you have an upcoming payment:</p>
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Contract:</strong> {contract_name}</p>
                <p style="margin: 5px 0;"><strong>Amount Due:</strong> {frappe.format_value(amount, 'Currency')}</p>
                <p style="margin: 5px 0;"><strong>Due Date:</strong> {frappe.format_value(due_date, 'Date')}</p>
            </div>
            <p>Please ensure timely payment to avoid late fees.</p>
            <a href="/customer-dashboard" style="display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 20px 0;">View Dashboard</a>
            <p style="color: #6b7280; font-size: 14px;">Thank you for your business!</p>
        </div>
        """
        
        frappe.sendmail(
            recipients=[customer.email],
            subject=subject,
            message=message,
            delayed=False
        )
        
    except Exception as e:
        frappe.log_error(f"Failed to send reminder: {str(e)}", "Payment Reminder Error")

def send_overdue_notice_to_customer(customer_profile, contract_name, count, total_amount):
    """Send overdue notice to customer"""
    try:
        customer = frappe.get_doc("Customer Profile", customer_profile)
        
        if not customer.email:
            return
        
        subject = f"Overdue Payment Notice - {contract_name}"
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #ef4444;">Payment Overdue</h2>
            <p>Dear {customer.full_name},</p>
            <p>You have <strong>{count}</strong> overdue payment(s) for contract {contract_name}.</p>
            <div style="background: #fee2e2; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ef4444;">
                <p style="margin: 5px 0;"><strong>Total Overdue Amount:</strong> {frappe.format_value(total_amount, 'Currency')}</p>
            </div>
            <p>Please make payment as soon as possible to avoid penalties.</p>
            <a href="/pay?contract={contract_name}" style="display: inline-block; background: #ef4444; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px; margin: 20px 0;">Pay Now</a>
        </div>
        """
        
        frappe.sendmail(
            recipients=[customer.email],
            subject=subject,
            message=message,
            delayed=False
        )
        
    except Exception as e:
        frappe.log_error(f"Failed to send overdue notice: {str(e)}", "Overdue Notice Error")

def notify_admin_overdue(contract_name, customer_profile, count, total_amount):
    """Notify admin about overdue payments"""
    try:
        customer = frappe.get_doc("Customer Profile", customer_profile)
        admins = get_admin_emails()
        
        if not admins:
            return
        
        subject = f"Overdue Alert - {contract_name}"
        message = f"""
        <h3>Overdue Payment Alert</h3>
        <p><strong>Contract:</strong> {contract_name}</p>
        <p><strong>Customer:</strong> {customer.full_name} ({customer.phone})</p>
        <p><strong>Overdue Installments:</strong> {count}</p>
        <p><strong>Total Amount:</strong> {frappe.format_value(total_amount, 'Currency')}</p>
        <p>Please follow up with the customer.</p>
        """
        
        frappe.sendmail(
            recipients=admins,
            subject=subject,
            message=message,
            delayed=False
        )
        
    except Exception as e:
        frappe.log_error(f"Failed to notify admin: {str(e)}", "Admin Notification Error")

def send_contract_confirmation(contract_doc):
    """Send contract confirmation email"""
    try:
        customer = frappe.get_doc("Customer Profile", contract_doc.customer)
        
        if not customer.email:
            return
        
        motorcycle = frappe.get_doc("Motorcycle", contract_doc.motorcycle)
        
        subject = f"Contract Confirmed - {contract_doc.name}"
        message = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #10b981;">✅ Contract Confirmed!</h2>
            <p>Dear {customer.full_name},</p>
            <p>Your motorcycle contract has been successfully created.</p>
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Motorcycle Details</h3>
                <p><strong>Brand:</strong> {motorcycle.brand}</p>
                <p><strong>Model:</strong> {motorcycle.model}</p>
                <p><strong>Plate Number:</strong> {motorcycle.plate_number}</p>
                
                <h3>Payment Terms</h3>
                <p><strong>Total Price:</strong> {frappe.format_value(contract_doc.total_price, 'Currency')}</p>
                <p><strong>Deposit:</strong> {frappe.format_value(contract_doc.deposit, 'Currency')}</p>
                <p><strong>Monthly Payment:</strong> {frappe.format_value(contract_doc.monthly_amount, 'Currency')}</p>
                <p><strong>Duration:</strong> {contract_doc.duration_months} months</p>
                <p><strong>Start Date:</strong> {frappe.format_value(contract_doc.start_date, 'Date')}</p>
            </div>
            <a href="/customer-dashboard" style="display: inline-block; background: #6366f1; color: white; padding: 12px 24px; text-decoration: none; border-radius: 8px;">View Contract</a>
        </div>
        """
        
        frappe.sendmail(
            recipients=[customer.email],
            subject=subject,
            message=message,
            delayed=False
        )
        
    except Exception as e:
        frappe.log_error(f"Failed to send confirmation: {str(e)}", "Contract Confirmation Error")

def get_weekly_summary():
    """Get weekly business summary"""
    from frappe.utils import add_days, nowdate
    
    week_start = add_days(nowdate(), -7)
    
    new_contracts = frappe.db.count("Contract", {
        "docstatus": 1,
        "creation": [">=", week_start]
    })
    
    payments = frappe.get_all("Payment", {
        "docstatus": 1,
        "payment_date": [">=", week_start]
    }, fields=["amount"])
    
    total_received = sum([flt(p.amount) for p in payments])
    
    overdue = frappe.db.count("Contract", {"status": "Active"})
    
    return {
        "new_contracts": new_contracts,
        "payments_count": len(payments),
        "total_received": total_received,
        "overdue_count": overdue
    }

def send_admin_weekly_report(summary):
    """Send weekly report to admin"""
    try:
        admins = get_admin_emails()
        
        if not admins:
            return
        
        subject = f"Weekly Business Summary - CycleTrack"
        message = f"""
        <h2>Weekly Summary</h2>
        <ul>
            <li><strong>New Contracts:</strong> {summary['new_contracts']}</li>
            <li><strong>Payments Received:</strong> {summary['payments_count']}</li>
            <li><strong>Total Revenue:</strong> {frappe.format_value(summary['total_received'], 'Currency')}</li>
            <li><strong>Active Overdue:</strong> {summary['overdue_count']}</li>
        </ul>
        """
        
        frappe.sendmail(
            recipients=admins,
            subject=subject,
            message=message,
            delayed=False
        )
        
    except Exception as e:
        frappe.log_error(f"Failed to send weekly report: {str(e)}", "Weekly Report Error")

def get_admin_emails():
    """Get all admin email addresses"""
    admins = frappe.get_all("User",
        filters={
            "enabled": 1,
            "name": ["!=", "Guest"]
        },
        fields=["email"])
    
    return [u.email for u in admins if u.email]