app_name = "cycle_track"
app_title = "CycleTrack"
app_publisher = "techberna"
app_version = "0.0.2"
app_icon = "octicon octicon-rocket"
app_color = "#5C6BC0"
app_description = "Motorcycle rental and financing management system"
app_email = "bernabazubagira@gmail.com"
app_license = "mit"

# ============================================================================
# SCHEDULER EVENTS
# ============================================================================

scheduler_events = {
    "daily": [
        "cycle_track.events.send_payment_reminders",
        "cycle_track.events.check_overdue_payments",
        "cycle_track.events.send_overdue_notices"
    ],
    "weekly": [
        "cycle_track.events.send_weekly_summary"
    ]
}

# ============================================================================
# ASSETS
# ============================================================================

# CSS - No leading slash!
app_include_css = "assets/cycle_track/css/cycle_track.css"

# JS - No leading slash!
app_include_js = "assets/cycle_track/js/cycle_track.js"

# ============================================================================
# API WHITELISTING
# ============================================================================

# These are automatically whitelisted via @frappe.whitelist() decorator in api.py
# No need to override here for v2 API

# ============================================================================
# WEBSITE ROUTES
# ============================================================================

website_route_rules = [
    # Customer routes
    {"from_route": "/motocycle", "to_route": "motocycle/index"},
    {"from_route": "/installments", "to_route": "installments/index"},
    {"from_route": "/payments", "to_route": "payments/index"},
    {"from_route": "/pay", "to_route": "pay/index"},
    {"from_route": "/customer_profile", "to_route": "customer_profile/index"},
    
    # Admin routes
    {"from_route": "/admin_dashboard", "to_route": "admin_dashboard/index"},
    {"from_route": "/admin_contracts", "to_route": "admin_contracts/index"},
    {"from_route": "/admin_customers", "to_route": "admin_customers/index"},
]

# ============================================================================
# ROLE-BASED HOME PAGES
# ============================================================================

role_home_page = {
    "Customer": "/customer_profile",
    "Administrator": "/admin_dashboard"
}

# ============================================================================
# DOCUMENT EVENTS
# ============================================================================

doc_events = {
    "Contract": {
        "on_submit": "cycle_track.events.on_contract_submit",
        "on_cancel": "cycle_track.events.on_contract_cancel"
    },
    "Payment": {
        "on_submit": "cycle_track.events.on_payment_submit"
    }
}

# ============================================================================
# DATABASE PATCHES
# ============================================================================

patches = ["cycle_track.patches.seed_demo.execute"]

# ============================================================================
# PERMISSIONS (Optional - for web portal access)
# ============================================================================

# Allow customers to access their own data via web portal
# web_form_accessible_doctype = [
#     "Customer Profile",
#     "Contract",
#     "Payment",
# ]

# ============================================================================
# FIXTURES (Optional - for syncing doctypes and custom fields)
# ============================================================================

# Sync these doctypes from files
# fixtures = [
#     "cycle_track.fixtures.custom_fields",
# ]

# ============================================================================
# TESTING (Optional - for automated tests)
# ============================================================================

# test_runner = "frappe.test_runner.TestRunner"
# test_suit = "tests"