app_name = "cycle_track"
app_title = "CycleTrack"
app_publisher = "techberna"
app_version = "0.0.1"
app_icon = "octicon octicon-rocket"
app_color = "#5C6BC0"
app_description = "web app that handles cycle managment"
app_email = "bernabazubagira@gmail.com"
app_license = "mit"

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

# CSS - Remove leading slash!
app_include_css = "assets/cycle_track/css/cycle_track.css"

# JS
app_include_js = "assets/cycle_track/js/cycle_track.js"

override_whitelisted_methods = {
    "cycle_track.api.get_admin_kpis": "cycle_track.page.admin_dashboard.admin_dashboard.get_admin_kpis"
}

website_route_rules = [
    # Customer routes
    {"from_route": "/contract", "to_route": "contract/index"},
    {"from_route": "/installments", "to_route": "installments/index"},
    {"from_route": "/payments", "to_route": "payments/index"},
    {"from_route": "/pay", "to_route": "pay/index"},
    {"from_route": "/customer_profile", "to_route": "customer_profile/index"},
    
    # Admin routes
    {"from_route": "/admin_dashboard", "to_route": "admin_dashboard/index"},
    {"from_route": "/admin_contracts", "to_route": "admin_contracts/index"},
    {"from_route": "/admin_customers", "to_route": "admin_customers/index"},
]

# Role-based home pages
role_home_page = {
    "Customer": "/customer_profile",
    "Administrator": "/admin_dashboard"
}
# Document Events
doc_events = {
    "Contract": {
        "on_submit": "cycle_track.events.on_contract_submit",
        "on_cancel": "cycle_track.events.on_contract_cancel"
    },
    "Payment": {
        "on_submit": "cycle_track.events.on_payment_submit"
    }
}

patches = ["cycle_track.patches.seed_demo.execute"]