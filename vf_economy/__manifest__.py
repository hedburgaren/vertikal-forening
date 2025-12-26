# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Economy Support",
    "summary": "Financial reports, payment views, and export-only access for treasurers",
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
        "vf_role",
        "vf_membership_fees",
        "account",
        "report_xlsx",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/report_template_data.xml",
        "views/vf_economy_report_views.xml",
        "views/vf_payment_view_views.xml",
        "views/vf_export_access_views.xml",
        "views/vf_member_views.xml",
        "report/report_templates.xml",
        "wizard/vf_payment_reminder_wizard_views.xml",
    ],
    "demo": [
        "demo/vf_economy_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_economy.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_economy/static/src/js/vf_economy.js",
        ],
    },
}
