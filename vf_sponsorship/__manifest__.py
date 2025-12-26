# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Sponsorship & Sales",
    "summary": "Sponsorship packages, sponsor communication, and merchandise sales management",
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
        "vf_template",
        "account",
        "sale_management",
        "website_sale",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/sponsorship_level_data.xml",
        "data/merchandise_category_data.xml",
        "views/vf_sponsor_views.xml",
        "views/vf_sponsorship_package_views.xml",
        "views/vf_sponsorship_contract_views.xml",
        "views/vf_merchandise_product_views.xml",
        "views/vf_merchandise_order_views.xml",
        "views/vf_partner_views.xml",
        "report/sponsorship_report_views.xml",
    ],
    "demo": [
        "demo/vf_sponsor_demo.xml",
        "demo/vf_sponsorship_package_demo.xml",
        "demo/vf_merchandise_product_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_sponsorship.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_sponsorship/static/src/js/vf_sponsorship.js",
        ],
        "web.assets_frontend": [
            "vf_sponsorship/static/src/js/vf_sponsorship_frontend.js",
            "vf_sponsorship/static/src/scss/vf_sponsorship_frontend.scss",
        ],
    },
}
