# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Document Management",
    "summary": "Document management with visibility levels and version control",
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
        "data/document_category_data.xml",
        "views/vf_document_category_views.xml",
        "views/vf_document_views.xml",
        "views/vf_document_version_views.xml",
        "views/ir_attachment_views.xml",
    ],
    "demo": [
        "demo/vf_document_category_demo.xml",
        "demo/vf_document_demo.xml",
        "demo/vf_document_template_demo.xml",
    ],
    "qweb": [
        "static/src/xml/vf_document.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vf_document/static/src/js/vf_document.js",
        ],
        "web.assets_frontend": [
            "vf_document/static/src/js/vf_document_frontend.js",
            "vf_document/static/src/scss/vf_document_frontend.scss",
        ],
    },
}
