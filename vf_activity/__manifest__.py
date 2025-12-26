# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Activities",
    "summary": "Activity management, scheduling, and resource booking",
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
        "vf_communication",
        "vf_document",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/activity_type_data.xml",
        "views/vf_activity_type_views.xml",
        "views/vf_activity_views.xml",
        "views/vf_activity_schedule_views.xml",
        "views/vf_resource_views.xml",
        "views/res_partner_views.xml",
    ],
    "demo": [
        "demo/vf_activity_type_demo.xml",
        "demo/vf_activity_demo.xml",
        "demo/vf_activity_schedule_demo.xml",
        "demo/vf_resource_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_activity.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_activity/static/src/js/vf_activity.js",
        ],
        "web.assets_frontend": [
            "vf_activity/static/src/js/vf_activity_frontend.js",
            "vf_activity/static/src/scss/vf_activity_frontend.scss",
        ],
    },
}
