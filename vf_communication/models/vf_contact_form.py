# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfContactForm(models.Model):
    _name = 'vf.contact.form'
    _description = 'Association Contact Form'
    _order = 'date desc'
    _rec_name = 'subject'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    subject = fields.Char(
        string='Subject',
        required=True,
        tracking=True
    )
    message = fields.Html(
        string='Message',
        required=True,
        tracking=True
    )
    
    # Sender information
    sender_name = fields.Char(
        string='Your Name',
        required=True,
        tracking=True
    )
    sender_email = fields.Char(
        string='Your Email',
        required=True,
        tracking=True
    )
    sender_phone = fields.Char(
        string='Your Phone',
        tracking=True
    )
    
    # Target
    mailbox_id = fields.Many2one(
        'vf.mailbox',
        string='Send To',
        required=True,
        tracking=True
    )
    
    # Status
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    state = fields.Selection([
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ], string='State', default='new', required=True, tracking=True)
    
    # Internal notes
    internal_notes = fields.Text(
        string='Internal Notes',
        tracking=True,
        groups='vf_base.vf_admin'
    )
    
    # Reference
    partner_id = fields.Many2one(
        'res.partner',
        string='Related Partner',
        tracking=True,
        help='Partner created from this contact form submission'
    )

    @api.constrains('sender_email')
    def _check_email(self):
        for form in self:
            if form.sender_email and not self.env['res.partner']._validate_email(form.sender_email):
                raise ValidationError(_('Invalid email address.'))

    def action_mark_read(self):
        """Mark the contact form as read"""
        self.write({'state': 'read'})
        return True

    def action_reply(self):
        """Open reply composer"""
        self.ensure_one()
        return {
            'name': _('Reply to Contact Form'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.mail',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_email_to': self.sender_email,
                'default_subject': _('Re: %s') % self.subject,
                'default_body_html': _(
                    '<p>Thank you for your message.</p>'
                    '<p>--- Original message ---</p>'
                    '<p>%s</p>'
                ) % self.message,
            },
        }

    def action_create_partner(self):
        """Create a partner from the contact form"""
        self.ensure_one()
        
        # Check if partner already exists
        partner = self.env['res.partner'].search([
            ('email', '=', self.sender_email)
        ], limit=1)
        
        if not partner:
            partner = self.env['res.partner'].create({
                'name': self.sender_name,
                'email': self.sender_email,
                'phone': self.sender_phone,
            })
        
        self.write({
            'partner_id': partner.id,
            'state': 'replied'
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Partner'),
            'res_model': 'res.partner',
            'res_id': partner.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_close(self):
        """Close the contact form"""
        self.write({'state': 'closed'})
        return True

    def action_forward_to_mailbox(self):
        """Forward the message to the mailbox recipients"""
        self.ensure_one()
        
        # Create message
        message = self.env['vf.message'].create({
            'subject': _('Contact Form: %s') % self.subject,
            'body': _(
                '<div>'
                '<p><strong>From:</strong> %s (%s)</p>'
                '<p><strong>Phone:</strong> %s</p>'
                '<p><strong>Date:</strong> %s</p>'
                '<hr/>'
                '<p>%s</p>'
                '</div>'
            ) % (
                self.sender_name,
                self.sender_email,
                self.sender_phone or _('Not provided'),
                self.date.strftime('%Y-%m-%d %H:%M'),
                self.message
            ),
            'sender_id': self.env.user.partner_id.id,
        })
        
        # Set recipients based on mailbox
        if self.mailbox_id.position_id:
            message.write({'recipient_position_ids': [(4, self.mailbox_id.position_id.id)]})
        elif self.mailbox_id.group_id:
            message.write({'recipient_group_ids': [(4, self.mailbox_id.group_id.id)]})
        elif self.mailbox_id.section_id:
            message.write({'recipient_section_ids': [(4, self.mailbox_id.section_id.id)]})
        
        # Send the message
        message.action_send()
        
        self.write({'state': 'replied'})
        
        return True
