# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Role Management",
    "summary": "Role-based access control with time-limited mandates",
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
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/role_data.xml",
        "views/vf_role_views.xml",
        "views/vf_position_views.xml",
        "views/vf_mandate_views.xml",
        "views/vf_mandate_extension_views.xml",
        "views/res_partner_views.xml",
    ],
    "demo": [
        "demo/vf_role_demo.xml",
        "demo/vf_position_demo.xml",
        "demo/vf_mandate_demo.xml",
    ],
}
