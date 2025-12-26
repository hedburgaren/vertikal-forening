# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Attendance & Reporting",
    "summary": "Advanced attendance tracking, reporting tools, and analytics dashboards",
    "version": "18.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Association",
    "author": "Vertikal Forening",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "vf_base",
        "vf_member",
        "vf_group",
        "vf_activity",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/report_template_data.xml",
        "views/vf_attendance_report_views.xml",
        "views/vf_attendance_summary_views.xml",
        "views/vf_member_views.xml",
        "views/vf_group_views.xml",
        "views/vf_activity_views.xml",
    ],
    "demo": [
        "demo/vf_attendance_report_demo.xml",
        "demo/vf_attendance_summary_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_attendance_reporting.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_attendance_reporting/static/src/js/vf_attendance_reporting.js",
        ],
    },
}
