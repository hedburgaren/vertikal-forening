# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfMailbox(models.Model):
    _name = 'vf.mailbox'
    _description = 'Association Mailbox'
    _order = 'name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Mailbox Name',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help='Unique code for email addressing'
    )
    
    # Scope definition
    position_id = fields.Many2one(
        'vf.position',
        string='Position',
        tracking=True,
        help='Mailbox for this position'
    )
    group_id = fields.Many2one(
        'vf.group',
        string='Group',
        tracking=True,
        help='Mailbox for this group'
    )
    section_id = fields.Many2one(
        'vf.section',
        string='Section',
        tracking=True,
        help='Mailbox for this section'
    )
    
    # Email configuration
    email = fields.Char(
        string='Email Address',
        tracking=True,
        help='External email address (if different from generated)'
    )
    notification_email = fields.Char(
        string='Notification Email',
        tracking=True,
        help='Send notifications to this email'
    )
    
    # Access control
    allowed_user_ids = fields.Many2many(
        'res.users',
        'vf_mailbox_user_rel',
        'mailbox_id',
        'user_id',
        string='Allowed Users',
        tracking=True
    )
    allowed_group_ids = fields.Many2many(
        'res.groups',
        'vf_mailbox_group_rel',
        'mailbox_id',
        'group_id',
        string='Allowed Groups',
        tracking=True
    )
    
    # Status
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    current_holders = fields.Text(
        compute='_compute_current_holders',
        string='Current Holders'
    )
    
    # Statistics
    message_count = fields.Integer(
        string='Messages',
        compute='_compute_message_count',
        store=True
    )
    unread_count = fields.Integer(
        string='Unread',
        compute='_compute_unread_count',
        store=True
    )
    
    # Constraints
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Mailbox code must be unique!'),
    ]

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for mailbox in self:
            mailbox.display_name = f'{mailbox.name} ({mailbox.code})'

    @api.depends('position_id', 'group_id', 'section_id')
    def _compute_current_holders(self):
        for mailbox in self:
            holders = []
            
            if mailbox.position_id:
                mandates = self.env['vf.mandate'].search([
                    ('position_id', '=', mailbox.position_id.id),
                    ('status', '=', 'active')
                ])
                holders.extend([m.person_id.name for m in mandates])
            
            elif mailbox.group_id:
                leaders = self.env['vf.group.leadership'].search([
                    ('group_id', '=', mailbox.group_id.id),
                    ('is_active', '=', True)
                ])
                holders.extend([l.leader_id.name for l in leaders])
            
            elif mailbox.section_id and mailbox.section_id.manager_id:
                holders.append(mailbox.section_id.manager_id.name)
            
            mailbox.current_holders = ', '.join(holders) if holders else 'No current holders'

    @api.depends('contact_form_ids')
    def _compute_message_count(self):
        for mailbox in self:
            mailbox.message_count = len(mailbox.contact_form_ids)

    @api.depends('contact_form_ids.state')
    def _compute_unread_count(self):
        for mailbox in self:
            mailbox.unread_count = len(mailbox.contact_form_ids.filtered(
                lambda f: f.state in ['new']
            ))

    @api.constrains('position_id', 'group_id', 'section_id')
    def _check_scope(self):
        """Only one scope can be defined"""
        for mailbox in self:
            scopes = sum([
                bool(mailbox.position_id),
                bool(mailbox.group_id),
                bool(mailbox.section_id),
            ])
            if scopes > 1:
                raise ValidationError(_('A mailbox can only be assigned to one scope (position, group, or section).'))

    @api.constrains('position_id', 'group_id', 'section_id')
    def _check_scope_consistency(self):
        """Check that group belongs to section if both are defined"""
        for mailbox in self:
            if mailbox.group_id and mailbox.section_id:
                if mailbox.group_id.section_id != mailbox.section_id:
                    raise ValidationError(_('Group must belong to the selected section.'))

    def action_view_messages(self):
        """View contact forms sent to this mailbox"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_contact_form_action').read()[0]
        action['domain'] = [('mailbox_id', '=', self.id)]
        return action

    def action_compose_email(self):
        """Compose email to mailbox recipients"""
        self.ensure_one()
        
        # Get recipients
        recipients = []
        
        if self.position_id:
            mandates = self.env['vf.mandate'].search([
                ('position_id', '=', self.position_id.id),
                ('status', '=', 'active')
            ])
            recipients = [m.person_id.email for m in mandates if m.person_id.email]
        
        elif self.group_id:
            leaders = self.env['vf.group.leadership'].search([
                ('group_id', '=', self.group_id.id),
                ('is_active', '=', True)
            ])
            recipients = [l.leader_id.email for l in leaders if l.leader_id.email]
        
        elif self.section_id and self.section_id.manager_id:
            if self.section_id.manager_id.email:
                recipients = [self.section_id.manager_id.email]
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Compose Email'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_composition_mode': 'mass_mail',
                'default_notify': True,
                'default_partner_ids': recipients,
                'default_subject': _('Email from %s') % self.name,
            },
        }

    @api.model
    def get_mailbox_for_user(self, user_id):
        """Get all mailboxes a user has access to"""
        user = self.env['res.users'].browse(user_id)
        
        # Direct access
        mailboxes = self.search([
            ('allowed_user_ids', 'in', [user_id]),
            ('active', '=', True)
        ])
        
        # Group access
        for group in user.groups_id:
            mailboxes |= self.search([
                ('allowed_group_ids', 'in', [group.id]),
                ('active', '=', True)
            ])
        
        return mailboxes

    def generate_email_address(self):
        """Generate email address from code"""
        for mailbox in self:
            if not mailbox.email:
                # Generate based on domain configuration
                domain = self.env['ir.config_parameter'].sudo().get_param('mail.catchall.domain')
                if domain:
                    mailbox.email = f'{mailbox.code}@{domain}'
        return True
