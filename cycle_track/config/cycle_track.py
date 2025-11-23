from frappe import _

def get_data():
    return [
        {
            "module_name": "CycleTrack",
            "type": "module",
            "label": _("Cycle Track"),
            "icon": "octicon octicon-rocket",
            "color": "#5C6BC0",
            "onboard_present": False,
            "app_name": "cycle_track"
        }
    ]
