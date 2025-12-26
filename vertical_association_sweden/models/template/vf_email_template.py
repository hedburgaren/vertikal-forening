# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfEmailTemplate(models.Model):
    _name = 'vf.email.template'
    _description = 'Email Template'
    _order = 'category_id, name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Template Name',
        required=True,
        tracking=True,
        translate=True
    )
    description = fields.Text(
        string='Description',
        tracking=True,
        translate=True
    )
    category_id = fields.Many2one(
        'vf.template.category',
        string='Category',
        required=True,
        domain="[('template_type', '=', 'email')]",
        tracking=True
    )
    
    # Template type
    email_type = fields.Selection([
        ('notification', 'Notification Template'),
        ('reminder', 'Reminder Template'),
        ('confirmation', 'Confirmation Template'),
        ('welcome', 'Welcome Template'),
        ('invoice', 'Invoice Template'),
        ('custom', 'Custom Template'),
    ], string='Email Type', required=True, default='notification')
    
    # Email content
    subject = fields.Char(
        string='Subject',
        required=True,
        tracking=True,
        translate=True
    )
    body_html = fields.Html(
        string='HTML Body',
        required=True,
        tracking=True,
        translate=True
    )
    body_text = fields.Text(
        string='Text Body',
        tracking=True,
        translate=True,
        help='Plain text version for email clients that don\'t support HTML'
    )
    
    # Sender settings
    sender_id = fields.Many2one(
        'res.partner',
        string='Default Sender',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    sender_email = fields.Char(
        string='Sender Email',
        tracking=True,
        help='Override sender email address'
    )
    reply_to = fields.Char(
        string='Reply To',
        tracking=True
    )
    
    # Attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'vf_email_template_attachment_rel',
        'template_id',
        'attachment_id',
        string='Default Attachments'
    )
    
    # Variables and sample data
    variable_ids = fields.Many2many(
        'vf.template.variable',
        'vf_email_template_variable_rel',
        'template_id',
        'variable_id',
        string='Variables'
    )
    sample_data = fields.Text(
        string='Sample Data',
        help='JSON sample data for preview'
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
    usage_count = fields.Integer(
        string='Usage Count',
        compute='_compute_usage_count',
        store=True
    )
    
    # Multilingual support
    lang_ids = fields.Many2many(
        'res.lang',
        'vf_email_template_lang_rel',
        'template_id',
        'lang_id',
        string='Available Languages'
    )

    @api.depends('name', 'category_id')
    def _compute_display_name(self):
        for template in self:
            if template.category_id:
                template.display_name = f'{template.category_id.name} / {template.name}'
            else:
                template.display_name = template.name

    @api.depends('sent_email_ids')
    def _compute_usage_count(self):
        for template in self:
            template.usage_count = len(template.sent_email_ids)

    def action_preview(self):
        """Preview the email template"""
        self.ensure_one()
        return {
            'name': _('Preview Email'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.template.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_template_model': 'vf.email.template',
            },
        }

    def action_send_test(self):
        """Send test email to current user"""
        self.ensure_one()
        
        # Create mail.mail record
        mail_values = {
            'subject': self._render_template(self.subject, 'test'),
            'body_html': self._render_template(self.body_html, 'test'),
            'body_text': self._render_template(self.body_text or '', 'test'),
            'email_from': self.sender_email or self.sender_id.email or self.env.user.email,
            'email_to': self.env.user.email,
            'reply_to': self.reply_to,
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Email Sent'),
                'message': _('Test email has been sent to %s' % self.env.user.email),
                'type': 'success',
            }
        }

    def _render_template(self, template, record):
        """Render template with variables"""
        try:
            # Simple rendering - in practice, you'd use proper Jinja2
            return template
        except Exception:
            return template

    def send_email(self, recipients, data=None):
        """Send email to recipients"""
        self.ensure_one()
        
        if not recipients:
            raise ValidationError(_('No recipients specified'))
        
        # Prepare email values
        mail_values = {
            'subject': self._render_template(self.subject, data),
            'body_html': self._render_template(self.body_html, data),
            'body_text': self._render_template(self.body_text or '', data),
            'email_from': self.sender_email or self.sender_id.email or self.env.user.email,
            'reply_to': self.reply_to,
            'attachment_ids': [(6, 0, self.attachment_ids.ids)],
        }
        
        # Create and send emails
        mails = []
        for recipient in recipients:
            values = mail_values.copy()
            values['email_to'] = recipient
            mail = self.env['mail.mail'].create(values)
            mails.append(mail)
        
        # Send all emails
        self.env['mail.mail'].browse([m.id for m in mails]).send()
        
        # Track usage
        self.env['vf.email.usage'].create({
            'template_id': self.id,
            'recipient_count': len(recipients),
            'sent_date': fields.Datetime.now(),
            'sent_by': self.env.user.id,
        })
        
        return True

    def get_variables(self):
        """Get all variables used in this template"""
        variables = []
        
        # Extract from subject
        import re
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, self.subject or '')
        variables.extend(matches)
        
        # Extract from body_html
        matches = re.findall(pattern, self.body_html or '')
        variables.extend(matches)
        
        # Extract from body_text
        matches = re.findall(pattern, self.body_text or '')
        variables.extend(matches)
        
        # Return unique variables
        return list(set(variables))
