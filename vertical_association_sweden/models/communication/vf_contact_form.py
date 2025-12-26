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
    
    # Status and tracking
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        readonly=True
    )
    state = fields.Selection([
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('closed', 'Closed'),
    ], string='Status', default='new', required=True, tracking=True)
    
    # Processing
    assigned_to = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True
    )
    reply_message = fields.Html(
        string='Reply Message',
        tracking=True
    )
    reply_date = fields.Datetime(
        string='Reply Date',
        readonly=True
    )
    
    # Categorization
    category_id = fields.Many2one(
        'vf.contact.category',
        string='Category',
        tracking=True
    )
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='normal', required=True, tracking=True)
    
    # Attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'vf_contact_form_attachment_rel',
        'form_id',
        'attachment_id',
        string='Attachments'
    )

    @api.constrains('sender_email')
    def _check_email(self):
        for form in self:
            if form.sender_email and '@' not in form.sender_email:
                raise ValidationError(_('Please enter a valid email address.'))

    def action_mark_read(self):
        """Mark the form as read"""
        self.write({
            'state': 'read',
            'assigned_to': self.env.user,
        })
        return True

    def action_reply(self):
        """Open reply wizard"""
        self.ensure_one()
        return {
            'name': _('Reply to Contact Form'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.contact.form.reply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_form_id': self.id},
        }

    def action_close(self):
        """Close the contact form"""
        self.write({'state': 'closed'})
        return True

    def action_reopen(self):
        """Reopen the contact form"""
        self.write({'state': 'read'})
        return True

    def _send_notification(self):
        """Send notification to mailbox responsible"""
        if self.mailbox_id.notification_email:
            template = self.env.ref('vertical_association_sweden.email_template_contact_form_notification')
            template.send_mail(self.id, force_send=True)

    @api.model
    def create(self, vals):
        form = super().create(vals)
        form._send_notification()
        return form
