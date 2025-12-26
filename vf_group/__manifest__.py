# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association - Group Management",
    "summary": "Groups, sections and organizational structure for associations",
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
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/group_type_data.xml",
        "views/vf_section_views.xml",
        "views/vf_group_views.xml",
        "views/vf_group_membership_views.xml",
    ],
    "demo": [
        "demo/vf_section_demo.xml",
        "demo/vf_group_demo.xml",
        "demo/vf_group_membership_demo.xml",
    ],
}
