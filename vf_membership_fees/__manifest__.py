# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Membership Fees",
    "summary": "Membership fee management, invoicing, and payment tracking",
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
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/fee_category_data.xml",
        "data/email_template_data.xml",
        "views/vf_fee_category_views.xml",
        "views/vf_fee_views.xml",
        "views/vf_fee_payment_views.xml",
        "views/vf_fee_waiver_views.xml",
        "views/vf_member_views.xml",
    ],
    "demo": [
        "demo/vf_fee_category_demo.xml",
        "demo/vf_fee_demo.xml",
        "demo/vf_fee_payment_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_membership_fees.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_membership_fees/static/src/js/vf_membership_fees.js",
        ],
        "web.assets_frontend": [
            "vf_membership_fees/static/src/js/vf_membership_fees_frontend.js",
            "vf_membership_fees/static/src/scss/vf_membership_fees_frontend.scss",
        ],
    },
    "post_init_hook": "post_init_hook",
}
