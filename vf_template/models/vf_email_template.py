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
        string='Body',
        required=True,
        tracking=True,
        translate=True
    )
    body_text = fields.Text(
        string='Plain Text Body',
        help='Plain text version for email clients that don\'t support HTML',
        translate=True
    )
    
    # Sender settings
    default_from = fields.Char(
        string='Default From',
        help='Default sender email. If empty, uses Odoo default.'
    )
    reply_to = fields.Char(
        string='Reply To',
        help='Reply-to email address'
    )
    
    # Attachments
    default_attachment_ids = fields.Many2many(
        'ir.attachment',
        'vf_email_template_attachment_rel',
        'template_id',
        'attachment_id',
        string='Default Attachments'
    )
    
    # Variables and dynamic content
    variable_ids = fields.One2many(
        'vf.template.variable',
        'email_template_id',
        string='Variables'
    )
    
    # Multilingual support
    available_languages = fields.Many2many(
        'res.lang',
        'vf_email_template_lang_rel',
        'template_id',
        'lang_id',
        string='Available Languages',
        default=lambda self: self.env['res.lang'].search([('active', '=', True)])
    )
    
    # Usage tracking
    usage_count = fields.Integer(
        string='Usage Count',
        readonly=True
    )
    last_used = fields.Datetime(
        string='Last Used',
        readonly=True
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    _sql_constraints = [
        ('name_unique_category', 'unique(name, category_id)', 
         'Template name must be unique within category!'),
    ]

    @api.depends('name', 'category_id')
    def _compute_display_name(self):
        for template in self:
            if template.category_id:
                template.display_name = f'{template.category_id.name} / {template.name}'
            else:
                template.display_name = template.name

    def action_send_test(self):
        """Send test email to current user"""
        self.ensure_one()
        
        if not self.env.user.email:
            raise ValidationError(_('You must have an email address to receive test emails.'))
        
        # Prepare context with test data
        test_context = {
            'member_name': self.env.user.name,
            'membership_number': 'TEST123',
            'date': fields.Date.today().strftime('%d/%m/%Y'),
            'association_name': 'Vertical Association',
            'email': self.env.user.email,
        }
        
        # Send email
        mail_values = {
            'subject': self._render_template(self.subject, test_context),
            'body_html': self._render_template(self.body_html, test_context),
            'body_text': self._render_template(self.body_text or '', test_context),
            'email_to': self.env.user.email_formatted,
            'email_from': self.default_from or self.env.user.email_formatted,
            'reply_to': self.reply_to,
        }
        
        mail = self.env['mail.mail'].create(mail_values)
        mail.send()
        
        # Update usage tracking
        self.write({
            'usage_count': self.usage_count + 1,
            'last_used': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test Email Sent'),
                'message': _('Test email has been sent to %s') % self.env.user.email,
                'type': 'success',
            }
        }

    def action_preview(self):
        """Preview email template"""
        self.ensure_one()
        
        # Prepare test context
        test_context = {
            'member_name': 'John Doe',
            'membership_number': 'VF000001',
            'date': fields.Date.today().strftime('%d/%m/%Y'),
            'association_name': 'Vertical Association',
            'email': 'john.doe@example.com',
        }
        
        # Render content
        subject = self._render_template(self.subject, test_context)
        body_html = self._render_template(self.body_html, test_context)
        body_text = self._render_template(self.body_text or '', test_context)
        
        # Create preview
        preview = self.env['mail.compose.message'].create({
            'subject': subject,
            'body': body_html,
            'body_text': body_text,
            'composition_mode': 'comment',
            'model': 'vf.email.template',
            'res_id': self.id,
            'template_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Email Preview'),
            'res_model': 'mail.compose.message',
            'res_id': preview.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_preview_mode': True},
        }

    def _render_template(self, template, context):
        """Render template with context variables"""
        if not template:
            return ''
        
        # Simple variable replacement
        for key, value in context.items():
            template = template.replace(f'{{{{{key}}}}}', str(value))
        
        # TODO: Implement proper Jinja2 template rendering
        # This is a simplified version for now
        
        return template

    def action_translate(self):
        """Open translation view for this template"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Translate Template'),
            'res_model': 'base.language.export',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_lang': self.env.user.lang,
                'default_data': [{
                    'model': self._name,
                    'res_id': self.id,
                }]
            },
        }

    def action_duplicate(self):
        """Duplicate template"""
        self.ensure_one()
        
        self.copy({
            'name': _('%s (copy)') % self.name,
            'usage_count': 0,
            'last_used': False,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Template Duplicated'),
                'message': _('Template has been duplicated successfully'),
                'type': 'success',
            }
        }
