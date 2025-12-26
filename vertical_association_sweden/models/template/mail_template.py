# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    # Vertical Association specific fields
    vf_template_id = fields.Many2one(
        'vf.email.template',
        string='VF Email Template',
        help='Link to Vertical Association email template for additional features'
    )
    vf_layout_id = fields.Many2one(
        'vf.communication.layout',
        string='Communication Layout',
        domain="[('layout_type', '=', 'email')]",
        help='Layout to use for rendering this email'
    )
    
    # Association context
    is_association_template = fields.Boolean(
        string='Association Template',
        default=False,
        help='Mark this as an association-specific template'
    )
    
    # Additional variables
    association_variables = fields.Text(
        string='Association Variables',
        help='Additional variables available in this template (JSON format)'
    )
    
    @api.onchange('vf_template_id')
    def _onchange_vf_template_id(self):
        """Update fields from VF email template"""
        if self.vf_template_id:
            self.subject = self.vf_template_id.subject
            self.body_html = self.vf_template_id.body_html
            self.body_text = self.vf_template_id.body_text
            self.email_from = self.vf_template_id.default_from
            self.reply_to = self.vf_template_id.reply_to
            self.attachment_ids = self.vf_template_id.default_attachment_ids

    def generate_email(self, res_ids, fields=None):
        """Override to apply VF layout if specified"""
        result = super().generate_email(res_ids, fields)
        
        if self.vf_layout_id:
            for res_id in res_ids:
                if str(res_id) in result:
                    email_data = result[str(res_id)]
                    # Apply layout wrapper
                    email_data['body_html'] = self._apply_layout(email_data.get('body_html', ''))
                    result[str(res_id)] = email_data
        
        return result

    def _apply_layout(self, body_html):
        """Apply communication layout to email body"""
        if not self.vf_layout_id:
            return body_html
        
        layout = self.vf_layout_id
        
        # Build complete email with layout
        complete_html = ""
        
        # Header
        if layout.header_html:
            complete_html += layout.header_html
        
        # Wrapper with styles
        complete_html += f'<div style="{layout.email_wrapper_style or "max-width: 600px; margin: 0 auto;"}">'
        complete_html += f'<div style="{layout.email_body_style or "padding: 20px; background: white;"}">'
        complete_html += body_html or ''
        complete_html += '</div></div>'
        
        # Footer
        if layout.footer_html:
            complete_html += layout.footer_html
        
        return complete_html

    def send_mail(self, res_id, force_send=False, raise_exception=False, email_values=None):
        """Override to track usage if linked to VF template"""
        result = super().send_mail(res_id, force_send, raise_exception, email_values)
        
        # Update usage tracking for VF template
        if self.vf_template_id:
            self.vf_template_id.write({
                'usage_count': self.vf_template_id.usage_count + 1,
                'last_used': fields.Datetime.now(),
            })
        
        return result
