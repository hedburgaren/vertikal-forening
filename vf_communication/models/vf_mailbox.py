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
        compute='_compute_email',
        store=True
    )
    forward_to_personal = fields.Boolean(
        string='Forward to Personal Email',
        default=True,
        tracking=True,
        help='Forward messages to holders\' personal email addresses'
    )
    
    # Access control
    allowed_sender_ids = fields.Many2many(
        'res.partner',
        'vf_mailbox_sender_rel',
        'mailbox_id',
        'partner_id',
        string='Allowed Senders',
        help='Partners allowed to send to this mailbox (empty = all members)'
    )
    require_membership = fields.Boolean(
        string='Require Membership',
        default=True,
        tracking=True,
        help='Only association members can send to this mailbox'
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
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
        ('check_scope', 
         'CHECK((position_id IS NOT NULL) + (group_id IS NOT NULL) + '
         '(section_id IS NOT NULL) = 1)', 
         'Exactly one scope must be defined!'),
    ]

    @api.depends('name', 'code', 'position_id', 'group_id', 'section_id')
    def _compute_display_name(self):
        for mailbox in self:
            parts = [mailbox.name]
            if mailbox.position_id:
                parts.append(f'({mailbox.position_id.name})')
            elif mailbox.group_id:
                parts.append(f'({mailbox.group_id.name})')
            elif mailbox.section_id:
                parts.append(f'({mailbox.section_id.name})')
            mailbox.display_name = ' '.join(parts)

    @api.depends('code')
    def _compute_email(self):
        for mailbox in self:
            if mailbox.code:
                # Get domain from config or use default
                domain = self.env['ir.config_parameter'].sudo().get_param(
                    'vf_communication.email_domain', 'association.local'
                )
                mailbox.email = f'{mailbox.code}@{domain}'
            else:
                mailbox.email = False

    @api.depends('position_id', 'group_id', 'section_id')
    def _compute_current_holders(self):
        for mailbox in self:
            holders = []
            
            if mailbox.position_id:
                mandates = self.env['vf.mandate'].search([
                    ('position_id', '=', mailbox.position_id.id),
                    ('status', '=', 'active')
                ])
                holders = [m.person_id.name for m in mandates]
            
            elif mailbox.group_id:
                if mailbox.group_id.leader_id:
                    holders.append(mailbox.group_id.leader_id.name)
            
            elif mailbox.section_id:
                if mailbox.section_id.manager_id:
                    holders.append(mailbox.section_id.manager_id.name)
            
            mailbox.current_holders = ', '.join(holders) if holders else 'No active holders'

    @api.constrains('allowed_sender_ids')
    def _check_allowed_senders(self):
        for mailbox in self:
            if mailbox.allowed_sender_ids:
                # Check if all allowed senders are members or have special access
                for partner in mailbox.allowed_sender_ids:
                    if not partner.member_id and not partner.has_active_mandates:
                        raise ValidationError(_(
                            'Allowed sender %s must be a member or have an active mandate.'
                        ) % partner.name)

    def action_send_message(self):
        """Open compose message wizard pre-filled with this mailbox"""
        self.ensure_one()
        return {
            'name': _('Send Message'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.message',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_recipient_position_ids': [self.position_id.id] if self.position_id else False,
                'default_recipient_group_ids': [self.group_id.id] if self.group_id else False,
                'default_recipient_section_ids': [self.section_id.id] if self.section_id else False,
            },
        }

    def get_recipients(self):
        """Get all current mailbox recipients"""
        recipients = self.env['res.partner']
        
        if self.position_id:
            mandates = self.env['vf.mandate'].search([
                ('position_id', '=', self.position_id.id),
                ('status', '=', 'active')
            ])
            recipients = mandates.mapped('person_id')
        
        elif self.group_id:
            # Group leader and all members
            if self.group_id.leader_id:
                recipients |= self.group_id.leader_id
            memberships = self.env['vf.group.membership'].search([
                ('group_id', '=', self.group_id.id),
                ('is_active', '=', True)
            ])
            recipients |= memberships.mapped('member_id.partner_id')
        
        elif self.section_id:
            # Section manager and all section members
            if self.section_id.manager_id:
                recipients |= self.section_id.manager_id
            members = self.section_id.group_ids.mapped('member_ids').mapped('member_id')
            recipients |= members.mapped('partner_id')
        
        return recipients

    @api.model
    def get_mailbox_by_email(self, email):
        """Find mailbox by email address"""
        local_part = email.split('@')[0] if '@' in email else email
        return self.search([('code', '=', local_part), ('active', '=', True)])

    def check_can_send(self, partner):
        """Check if partner can send to this mailbox"""
        # Check if sender restriction exists
        if self.allowed_sender_ids:
            if partner not in self.allowed_sender_ids:
                return False, _('You are not allowed to send to this mailbox.')
        
        # Check membership requirement
        if self.require_membership:
            if not partner.member_id and not partner.has_active_mandates:
                return False, _('Only association members can send to this mailbox.')
        
        return True, ''
