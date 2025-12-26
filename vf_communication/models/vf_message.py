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
    recipient_role_ids = fields.Many2many(
        'vf.role',
        'vf_message_role_rel',
        'message_id',
        'role_id',
        string='To Roles',
        tracking=True
    )
    recipient_position_ids = fields.Many2many(
        'vf.position',
        'vf_message_position_rel',
        'message_id',
        'position_id',
        string='To Positions',
        tracking=True
    )
    
    # Status and configuration
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Options
    allow_reply = fields.Boolean(
        string='Allow Reply',
        default=True,
        tracking=True
    )
    send_email = fields.Boolean(
        string='Send Email Copy',
        help='Send email copy to recipients if they have email addresses',
        tracking=True
    )
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='normal', tracking=True)
    
    # Computed fields
    recipient_count = fields.Integer(
        string='Recipient Count',
        compute='_compute_recipient_count',
        store=True
    )
    has_attachments = fields.Boolean(
        compute='_compute_has_attachments'
    )
    
    # Relationships
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'vf_message_attachment_rel',
        'message_id',
        'attachment_id',
        string='Attachments'
    )
    
    _sql_constraints = [
        ('check_recipients', 
         'CHECK(recipient_ids != NULL OR recipient_group_ids != NULL OR '
         'recipient_section_ids != NULL OR recipient_role_ids != NULL OR '
         'recipient_position_ids != NULL)', 
         'At least one recipient must be specified!'),
    ]

    @api.depends('recipient_ids', 'recipient_group_ids', 'recipient_section_ids', 
                 'recipient_role_ids', 'recipient_position_ids')
    def _compute_recipient_count(self):
        for message in self:
            count = len(message.recipient_ids)
            
            # Add group members
            for group in message.recipient_group_ids:
                count += group.active_member_count
            
            # Add section members
            for section in message.recipient_section_ids:
                count += section.member_count
            
            # Add role holders
            for role in message.recipient_role_ids:
                # Count active mandates for this role
                mandates = self.env['vf.mandate'].search([
                    ('position_id.role_id', '=', role.id),
                    ('status', '=', 'active')
                ])
                count += len(mandates)
            
            # Add position holders
            for position in message.recipient_position_ids:
                count += position.current_holder_count
            
            message.recipient_count = count

    @api.depends('attachment_ids')
    def _compute_has_attachments(self):
        for message in self:
            message.has_attachments = bool(message.attachment_ids)

    @api.onchange('recipient_group_ids', 'recipient_section_ids', 
                  'recipient_role_ids', 'recipient_position_ids')
    def _onchange_recipients(self):
        """Clear individual recipients when using group targeting"""
        if (self.recipient_group_ids or self.recipient_section_ids or 
            self.recipient_role_ids or self.recipient_position_ids):
            self.recipient_ids = False

    @api.onchange('recipient_ids')
    def _onchange_individual_recipients(self):
        """Clear group recipients when using individual targeting"""
        if self.recipient_ids:
            self.recipient_group_ids = False
            self.recipient_section_ids = False
            self.recipient_role_ids = False
            self.recipient_position_ids = False

    def action_send(self):
        """Send the message to all recipients"""
        self.ensure_one()
        
        # Get all recipients
        recipients = self._get_all_recipients()
        
        if not recipients:
            raise ValidationError(_('No recipients found for this message.'))
        
        # Create mail messages for each recipient
        for recipient in recipients:
            self.env['mail.message'].create({
                'model': 'res.partner',
                'res_id': recipient.id,
                'message_type': 'comment',
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'body': self.body,
                'subject': self.subject,
                'author_id': self.sender_id.id,
                'email_from': self.sender_id.email_formatted,
                'reply_to': self.sender_id.email_formatted,
            })
            
            # Send email if enabled and recipient has email
            if self.send_email and recipient.email:
                mail_values = {
                    'subject': self.subject,
                    'body_html': self.body,
                    'email_to': recipient.email_formatted,
                    'email_from': self.sender_id.email_formatted,
                }
                self.env['mail.mail'].create(mail_values).send()
        
        # Update state
        self.write({'state': 'sent'})
        
        # Post notification
        self.message_post(
            body=_('Message sent to %d recipients') % len(recipients),
            message_type='notification'
        )
        
        return True

    def _get_all_recipients(self):
        """Get all unique recipients based on targeting"""
        recipients = self.env['res.partner'].browse()
        
        # Direct recipients
        if self.recipient_ids:
            recipients |= self.recipient_ids
        
        # Group members
        if self.recipient_group_ids:
            for group in self.recipient_group_ids:
                memberships = self.env['vf.group.membership'].search([
                    ('group_id', '=', group.id),
                    ('is_active', '=', True)
                ])
                recipients |= memberships.mapped('member_id.partner_id')
        
        # Section members
        if self.recipient_section_ids:
            for section in self.recipient_section_ids:
                members = section.group_ids.mapped('member_ids').mapped('member_id')
                recipients |= members.mapped('partner_id')
        
        # Role holders
        if self.recipient_role_ids:
            for role in self.recipient_role_ids:
                mandates = self.env['vf.mandate'].search([
                    ('position_id.role_id', '=', role.id),
                    ('status', '=', 'active')
                ])
                recipients |= mandates.mapped('person_id')
        
        # Position holders
        if self.recipient_position_ids:
            for position in self.recipient_position_ids:
                mandates = self.env['vf.mandate'].search([
                    ('position_id', '=', position.id),
                    ('status', '=', 'active')
                ])
                recipients |= mandates.mapped('person_id')
        
        # Remove duplicates and sender
        recipients = recipients - self.sender_id
        
        return recipients

    def action_cancel(self):
        """Cancel the message"""
        self.write({'state': 'cancelled'})
        return True

    def action_set_to_draft(self):
        """Reset message to draft"""
        self.write({'state': 'draft'})
        return True

    def action_view_recipients(self):
        """Show all recipients in a tree view"""
        self.ensure_one()
        recipients = self._get_all_recipients()
        
        return {
            'name': _('Message Recipients'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', recipients.ids)],
            'context': {'form_view_initial_mode': 'readonly'},
        }
