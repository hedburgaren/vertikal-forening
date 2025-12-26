# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Template System",
    "summary": "Document templates, email templates, and communication layouts",
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
        "mail",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/template_category_data.xml",
        "views/vf_template_category_views.xml",
        "views/vf_document_template_views.xml",
        "views/vf_email_template_views.xml",
        "views/vf_communication_layout_views.xml",
        "views/mail_template_views.xml",
    ],
    "demo": [
        "demo/vf_template_category_demo.xml",
        "demo/vf_document_template_demo.xml",
        "demo/vf_email_template_demo.xml",
        "demo/vf_communication_layout_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_template.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_template/static/src/js/vf_template.js",
        ],
        "web.assets_frontend": [
            "vf_template/static/src/js/vf_template_frontend.js",
            "vf_template/static/src/scss/vf_template_frontend.scss",
        ],
    },
}
