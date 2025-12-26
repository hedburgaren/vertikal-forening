# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Vertical Association Sweden",
    "summary": "Complete association management system for Swedish associations",
    "version": "18.0.1.0.0",
    "development_status": "Production/Stable",
    "category": "Association",
    "author": "Vertikal Forening, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/vertical-association",
    "license": "AGPL-3",
    "application": True,
    "installable": True,
    "depends": [
        "base",
        "membership",
        "membership_extension",
        "mail",
        "account",
        "sale_management",
        "website",
        "portal",
        "documents",
        "report_xlsx",
    ],
    "data": [
        # Security
        "security/security.xml",
        "security/vf_member_security.xml",
        "security/vf_group_security.xml",
        "security/vf_role_security.xml",
        "security/vf_communication_security.xml",
        "security/vf_document_security.xml",
        "security/vf_template_security.xml",
        "security/vf_activity_security.xml",
        "security/vf_economy_security.xml",
        "security/vf_sponsorship_security.xml",
        "security/vf_portal_security.xml",
        "security/ir.model.access.csv",
        
        # Base Data
        "data/association_settings.xml",
        "data/relationship_type_data.xml",
        "data/group_type_data.xml",
        "data/role_data.xml",
        "data/activity_type_data.xml",
        "data/document_category_data.xml",
        "data/template_category_data.xml",
        
        # Member Views
        "views/member/vf_member_views.xml",
        "views/member/vf_household_views.xml",
        "views/member/vf_guardian_relationship_views.xml",
        "views/member/vf_family_relationship_views.xml",
        "views/member/res_partner_views.xml",
        
        # Group Views
        "views/group/vf_group_views.xml",
        "views/group/vf_section_views.xml",
        "views/group/vf_group_membership_views.xml",
        
        # Role Views
        "views/role/vf_role_views.xml",
        "views/role/vf_position_views.xml",
        "views/role/vf_mandate_views.xml",
        "views/role/vf_mandate_extension_views.xml",
        "views/role/res_partner_views.xml",
        
        # Communication Views
        "views/communication/vf_message_views.xml",
        "views/communication/vf_mailbox_views.xml",
        "views/communication/vf_contact_form_views.xml",
        "views/communication/res_partner_views.xml",
        
        # Document Views
        "views/document/vf_document_views.xml",
        "views/document/vf_document_category_views.xml",
        "views/document/vf_document_version_views.xml",
        "views/document/ir_attachment_views.xml",
        
        # Template Views
        "views/template/vf_template_category_views.xml",
        "views/template/vf_document_template_views.xml",
        "views/template/vf_email_template_views.xml",
        "views/template/vf_communication_layout_views.xml",
        "views/template/mail_template_views.xml",
        
        # Activity Views
        "views/activity/vf_activity_views.xml",
        "views/activity/vf_activity_type_views.xml",
        "views/activity/vf_activity_schedule_views.xml",
        "views/activity/vf_resource_views.xml",
        "views/activity/res_partner_views.xml",
        
        # Economy Views
        "views/economy/vf_economy_report_views.xml",
        "views/economy/vf_payment_view_views.xml",
        "views/economy/vf_export_access_views.xml",
        "views/economy/vf_member_views.xml",
        "views/economy/report/report_templates.xml",
        "views/economy/wizard/vf_payment_reminder_wizard_views.xml",
        
        # Sponsorship Views
        "views/sponsorship/vf_sponsor_views.xml",
        "views/sponsorship/vf_sponsorship_package_views.xml",
        "views/sponsorship/vf_sponsorship_contract_views.xml",
        "views/sponsorship/vf_merchandise_product_views.xml",
        "views/sponsorship/vf_merchandise_order_views.xml",
        "views/sponsorship/res_partner_views.xml",
        
        # Portal Views
        "views/portal/vf_portal_member_views.xml",
        "views/portal/vf_portal_activity_views.xml",
        "views/portal/vf_portal_document_views.xml",
        "views/portal/vf_portal_payment_views.xml",
        "views/portal/res_users_views.xml",
        "views/portal/website_templates.xml",
        
        # Menu Items
        "views/menus.xml",
    ],
    "demo": [
        # Demo Data
        "demo/vf_household_demo.xml",
        "demo/vf_member_demo.xml",
        "demo/vf_section_demo.xml",
        "demo/vf_group_demo.xml",
        "demo/vf_group_membership_demo.xml",
        "demo/vf_position_demo.xml",
        "demo/vf_mandate_demo.xml",
        "demo/vf_mailbox_demo.xml",
        "demo/vf_message_demo.xml",
        "demo/vf_document_demo.xml",
        "demo/vf_template_category_demo.xml",
        "demo/vf_document_template_demo.xml",
        "demo/vf_email_template_demo.xml",
        "demo/vf_communication_layout_demo.xml",
        "demo/vf_activity_type_demo.xml",
        "demo/vf_resource_demo.xml",
        "demo/vf_activity_demo.xml",
        "demo/vf_activity_schedule_demo.xml",
        "demo/vf_economy_demo.xml",
        "demo/vf_sponsorship_demo.xml",
        "demo/vf_portal_demo.xml",
        "demo/vf_role_demo.xml",
        "demo/vf_document_category_demo.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "vertical_association_sweden/static/src/js/*.js",
            "vertical_association_sweden/static/src/scss/*.scss",
        ],
        "web.assets_frontend": [
            "vertical_association_sweden/static/src/js/frontend/*.js",
            "vertical_association_sweden/static/src/scss/frontend/*.scss",
        ],
    },
}
