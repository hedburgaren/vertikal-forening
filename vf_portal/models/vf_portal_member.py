# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class VfPortalMember(models.Model):
    _name = 'vf.portal.member'
    _description = 'Portal Member Settings'
    _rec_name = 'member_id'

    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        ondelete='cascade'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Portal User',
        required=True,
        ondelete='cascade'
    )
    
    # Portal preferences
    allow_self_registration = fields.Boolean(
        string='Allow Self Registration',
        default=True,
        help='Allow member to register for activities themselves'
    )
    allow_document_access = fields.Boolean(
        string='Allow Document Access',
        default=True,
        help='Allow member to access documents based on their roles'
    )
    allow_payment_view = fields.Boolean(
        string='Allow Payment View',
        default=True,
        help='Allow member to view their payment history'
    )
    
    # Notification preferences
    email_notifications = fields.Boolean(
        string='Email Notifications',
        default=True,
        help='Receive email notifications for activities and updates'
    )
    sms_notifications = fields.Boolean(
        string='SMS Notifications',
        default=False,
        help='Receive SMS notifications for urgent updates'
    )
    
    # Privacy settings
    show_profile = fields.Boolean(
        string='Show Profile',
        default=False,
        help='Show member profile in member directory'
    )
    show_contact_info = fields.Boolean(
        string='Show Contact Info',
        default=False,
        help='Show contact information to other members'
    )
    
    # Dashboard preferences
    dashboard_layout = fields.Selection([
        ('default', 'Default'),
        ('compact', 'Compact'),
        ('detailed', 'Detailed'),
    ], string='Dashboard Layout', default='default')
    
    # Last activity
    last_login = fields.Datetime(
        string='Last Login',
        readonly=True
    )
    login_count = fields.Integer(
        string='Login Count',
        readonly=True,
        default=0
    )
    
    _sql_constraints = [
        ('unique_member', 'unique(member_id)', 
         'Member can only have one portal configuration!'),
        ('unique_user', 'unique(user_id)', 
         'User can only be linked to one member!'),
    ]

    @api.model
    def create_or_update_portal_member(self, member_id, user_id):
        """Create or update portal member configuration"""
        portal_member = self.search([('member_id', '=', member_id)], limit=1)
        
        if portal_member:
            portal_member.user_id = user_id
            return portal_member
        else:
            return self.create({
                'member_id': member_id,
                'user_id': user_id,
            })

    def action_update_last_login(self):
        """Update last login timestamp"""
        self.ensure_one()
        self.write({
            'last_login': fields.Datetime.now(),
            'login_count': self.login_count + 1,
        })

    def action_view_dashboard(self):
        """Open member dashboard"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/home',
            'target': 'self',
        }

    def action_edit_profile(self):
        """Open profile edit page"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Edit Profile',
            'res_model': 'vf.member',
            'res_id': self.member_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'edit',
            },
        }

    def action_view_my_activities(self):
        """View member's activity registrations"""
        self.ensure_one()
        
        registrations = self.env['vf.activity.registration'].search([
            ('member_id', '=', self.member_id.id)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Activities',
            'res_model': 'vf.activity.registration',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', registrations.ids)],
            'context': {
                'create': False,  # Read-only view
            },
        }

    def action_view_my_payments(self):
        """View member's payment history"""
        self.ensure_one()
        
        if not self.allow_payment_view:
            raise UserError(_('Payment access is not enabled for your account.'))
        
        fees = self.env['vf.fee'].search([
            ('member_id', '=', self.member_id.id)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Payments',
            'res_model': 'vf.fee',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', fees.ids)],
            'context': {
                'create': False,  # Read-only view
            },
        }
