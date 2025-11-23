import frappe

def get_context(context):
    # Check if user is admin
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login"
        raise frappe.Redirect
    
    # Check admin role
    user = frappe.get_doc("User", frappe.session.user)
    is_admin = any(role.role in ["Administrator", "Admin"] for role in user.roles)
    
    if not is_admin:
        frappe.throw("Access Denied: Admin role required")
    
    context.no_cache = 1
    return context