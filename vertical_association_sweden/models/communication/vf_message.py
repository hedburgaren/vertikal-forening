# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfMessage(models.Model):
    _name = 'vf.message'
    _description = 'Association Message'
    _order = 'date desc'
    _rec_name = 'subject'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    subject = fields.Char(
        string='Subject',
        required=True,
        tracking=True
    )
    body = fields.Html(
        string='Message',
        required=True,
        tracking=True
    )
    
    # Sender and recipients
    sender_id = fields.Many2one(
        'res.partner',
        string='From',
        required=True,
        default=lambda self: self.env.user.partner_id,
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Target selection (mutually exclusive)
    recipient_ids = fields.Many2many(
        'res.partner',
        'vf_message_recipient_rel',
        'message_id',
        'partner_id',
        string='To',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    recipient_group_ids = fields.Many2many(
        'vf.group',
        'vf_message_group_rel',
        'message_id',
        'group_id',
        string='To Groups',
        tracking=True
    )
    recipient_section_ids = fields.Many2many(
        'vf.section',
        'vf_message_section_rel',
        'message_id',
        'section_id',
        string='To Sections',
        tracking=True
    )
    recipient_type = fields.Selection([
        ('all', 'All Members'),
        ('individual', 'Individual Recipients'),
        ('group', 'Groups'),
        ('section', 'Sections'),
        ('role', 'Roles'),
    ], string='Recipient Type', required=True, default='individual')
    
    # Role-based targeting
    recipient_role_ids = fields.Many2many(
        'vf.role',
        'vf_message_role_rel',
        'message_id',
        'role_id',
        string='To Roles',
        tracking=True
    )
    
    # Delivery options
    send_email = fields.Boolean(
        string='Send Email',
        default=True,
        tracking=True
    )
    send_sms = fields.Boolean(
        string='Send SMS',
        tracking=True
    )
    send_portal = fields.Boolean(
        string='Send to Portal',
        default=True,
        tracking=True
    )
    
    # Status and tracking
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        readonly=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('scheduled', 'Scheduled'),
        ('failed', 'Failed'),
    ], string='Status', default='draft', required=True, tracking=True)
    scheduled_date = fields.Datetime(
        string='Scheduled For',
        tracking=True
    )
    
    # Statistics
    total_recipients = fields.Integer(
        string='Total Recipients',
        compute='_compute_total_recipients',
        store=True
    )
    sent_count = fields.Integer(
        string='Sent Count',
        compute='_compute_sent_count',
        store=True
    )
    failed_count = fields.Integer(
        string='Failed Count',
        compute='_compute_failed_count',
        store=True
    )
    
    # Delivery records
    delivery_ids = fields.One2many(
        'vf.message.delivery',
        'message_id',
        string='Deliveries'
    )
    
    # Template
    template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        tracking=True
    )
    
    # Attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'vf_message_attachment_rel',
        'message_id',
        'attachment_id',
        string='Attachments'
    )

    @api.depends('recipient_ids', 'recipient_group_ids', 'recipient_section_ids', 'recipient_role_ids', 'recipient_type')
    def _compute_total_recipients(self):
        for message in self:
            if message.recipient_type == 'all':
                message.total_recipients = self.env['vf.member'].search_count([])
            elif message.recipient_type == 'individual':
                message.total_recipients = len(message.recipient_ids)
            elif message.recipient_type == 'group':
                # Count unique members in all selected groups
                members = self.env['vf.member']
                for group in message.recipient_group_ids:
                    members |= group.member_ids
                message.total_recipients = len(members)
            elif message.recipient_type == 'section':
                # Count unique members in all selected sections
                members = self.env['vf.member']
                for section in message.recipient_section_ids:
                    members |= section.group_ids.mapped('member_ids')
                message.total_recipients = len(members)
            elif message.recipient_type == 'role':
                # Count unique members with selected roles
                partners = self.env['res.partner']
                for role in message.recipient_role_ids:
                    partners |= self.env['res.partner'].search([
                        ('mandate_ids.position_id.role_id', '=', role.id),
                        ('mandate_ids.status', '=', 'active')
                    ])
                message.total_recipients = len(partners)
            else:
                message.total_recipients = 0

    @api.depends('delivery_ids.state')
    def _compute_sent_count(self):
        for message in self:
            message.sent_count = len(message.delivery_ids.filtered(lambda d: d.state == 'sent'))

    @api.depends('delivery_ids.state')
    def _compute_failed_count(self):
        for message in self:
            message.failed_count = len(message.delivery_ids.filtered(lambda d: d.state == 'failed'))

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        for message in self:
            if message.scheduled_date and message.scheduled_date <= fields.Datetime.now():
                raise ValidationError(_('Scheduled date must be in the future.'))

    @api.onchange('recipient_type')
    def _onchange_recipient_type(self):
        """Clear recipient fields when type changes"""
        if self.recipient_type != 'individual':
            self.recipient_ids = False
        if self.recipient_type != 'group':
            self.recipient_group_ids = False
        if self.recipient_type != 'section':
            self.recipient_section_ids = False
        if self.recipient_type != 'role':
            self.recipient_role_ids = False

    def action_send(self):
        """Send the message to all recipients"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Only draft messages can be sent.'))
        
        # Get recipients based on type
        recipients = self._get_recipients()
        
        # Create delivery records
        for recipient in recipients:
            self.env['vf.message.delivery'].create({
                'message_id': self.id,
                'recipient_id': recipient.id,
                'send_email': self.send_email,
                'send_sms': self.send_sms,
                'send_portal': self.send_portal,
            })
        
        # Update state
        self.write({'state': 'sent', 'date': fields.Datetime.now()})
        
        # Process deliveries
        self.delivery_ids.action_process()
        
        return True

    def action_schedule(self):
        """Schedule the message for later sending"""
        self.ensure_one()
        if not self.scheduled_date:
            raise ValidationError(_('Please specify a scheduled date.'))
        
        self.write({'state': 'scheduled'})
        return True

    def action_test_send(self):
        """Send test message to current user"""
        self.ensure_one()
        
        delivery = self.env['vf.message.delivery'].create({
            'message_id': self.id,
            'recipient_id': self.env.user.partner_id.id,
            'send_email': self.send_email,
            'send_sms': self.send_sms,
            'send_portal': self.send_portal,
            'is_test': True,
        })
        
        delivery.action_process()
        return True

    def _get_recipients(self):
        """Get all recipients based on recipient type"""
        partners = self.env['res.partner']
        
        if self.recipient_type == 'all':
            members = self.env['vf.member'].search([])
            partners = members.mapped('partner_id')
        elif self.recipient_type == 'individual':
            partners = self.recipient_ids
        elif self.recipient_type == 'group':
            for group in self.recipient_group_ids:
                partners |= group.member_ids.mapped('partner_id')
        elif self.recipient_type == 'section':
            for section in self.recipient_section_ids:
                partners |= section.group_ids.mapped('member_ids').mapped('partner_id')
        elif self.recipient_type == 'role':
            for role in self.recipient_role_ids:
                partners |= self.env['res.partner'].search([
                    ('mandate_ids.position_id.role_id', '=', role.id),
                    ('mandate_ids.status', '=', 'active')
                ])
        
        return partners

    def action_view_deliveries(self):
        """View delivery status for this message"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_message_delivery_action').read()[0]
        action['domain'] = [('message_id', '=', self.id)]
        return action
