# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Communication",
    "summary": "Role-based messaging and internal communication system",
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
        "mail",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/email_template_data.xml",
        "views/vf_message_views.xml",
        "views/vf_mailbox_views.xml",
        "views/vf_contact_form_views.xml",
        "views/res_partner_views.xml",
    ],
    "demo": [
        "demo/vf_message_demo.xml",
        "demo/vf_mailbox_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_communication.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_communication/static/src/js/vf_communication.js",
        ],
        "web.assets_frontend": [
            "vf_communication/static/src/js/vf_communication_frontend.js",
            "vf_communication/static/src/scss/vf_communication_frontend.scss",
        ],
    },
}
