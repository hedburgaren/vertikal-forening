# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# Member models
from .member import vf_member
from .member import vf_household
from .member import vf_guardian_relationship
from .member import vf_family_relationship
from .member import vf_group_membership

# Group models
from .group import vf_group
from .group import vf_section
from .group import vf_group_leadership

# Role models
from .role import vf_position
from .role import vf_mandate
from .role import vf_emergency_access

# Communication models
from .communication import vf_message
from .communication import vf_message_recipient
from .communication import vf_contact_form
from .communication import res_partner

# Document models
from .document import vf_document
from .document import vf_document_version
from .document import vf_document_access

# Template models
from .template import vf_template_category
from .template import vf_document_template
from .template import vf_email_template
from .template import vf_communication_layout
from .template import vf_template_variable
from .template import mail_template

# Activity models
from .activity import vf_activity
from .activity import vf_activity_schedule
from .activity import vf_activity_registration
from .activity import vf_activity_attendance
from .activity import vf_resource

# Membership fee models
from .activity import vf_fee_category
from .activity import vf_fee
from .activity import vf_fee_payment
from .activity import vf_fee_waiver

# Economy models
from .economy import vf_economy_report
from .economy import vf_payment_view
from .economy import vf_export_access
from .economy import vf_payment_reminder_wizard

# Sponsorship models
from .sponsorship import vf_sponsor
from .sponsorship import vf_sponsorship_level
from .sponsorship import vf_sponsorship_benefit
from .sponsorship import vf_sponsorship_contract
from .sponsorship import vf_merchandise_category
from .sponsorship import vf_merchandise_product
from .sponsorship import vf_merchandise_order
from .sponsorship import vf_merchandise_order_line
from .sponsorship import res_partner

# Portal models
from .portal import vf_portal_member
from .portal import vf_portal_activity
from .portal import vf_activity_waiting_list
from .portal import vf_portal_document
from .portal import vf_portal_document_access
from .portal import vf_portal_document_category
from .portal import vf_portal_document_log
from .portal import vf_portal_payment
from .portal import vf_portal_payment_plan
from .portal import vf_portal_payment_plan_line
from .portal import res_users
