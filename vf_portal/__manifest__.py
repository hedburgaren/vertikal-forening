# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Member Portal",
    "summary": "Self-service member portal with event registration and document access",
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
        "vf_activity",
        "vf_membership_fees",
        "vf_sponsorship",
        "website",
        "website_membership",
        "portal",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/portal_menu_data.xml",
        "views/vf_portal_member_views.xml",
        "views/vf_portal_activity_views.xml",
        "views/vf_portal_document_views.xml",
        "views/vf_portal_payment_views.xml",
        "views/website_templates.xml",
        "controllers/main.py",
    ],
    "demo": [
        "demo/vf_portal_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_portal.xml",
        "static/src/xml/portal_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "vf_portal/static/src/scss/vf_portal.scss",
            "vf_portal/static/src/js/vf_portal.js",
            "vf_portal/static/src/js/vf_portal_member.js",
            "vf_portal/static/src/js/vf_portal_activity.js",
        ],
        "web.assets_backend": [
            "vf_portal/static/src/js/vf_portal_backend.js",
        ],
    },
}
