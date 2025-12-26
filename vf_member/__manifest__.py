# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Member Management",
    "summary": "Core member management with guardian relationships and family support",
    "version": "18.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Association",
    "author": "Vertikal Forening",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "contacts",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/relationship_type_data.xml",
        "views/vf_member_views.xml",
        "views/vf_guardian_relationship_views.xml",
        "views/vf_family_relationship_views.xml",
        "views/vf_household_views.xml",
        "views/res_partner_views.xml",
    ],
    "demo": [
        "demo/vf_member_demo.xml",
        "demo/vf_household_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_member.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_member/static/src/js/vf_member.js",
        ],
        "web.assets_frontend": [
            "vf_member/static/src/js/vf_member_frontend.js",
            "vf_member/static/src/scss/vf_member_frontend.scss",
        ],
    },
}
