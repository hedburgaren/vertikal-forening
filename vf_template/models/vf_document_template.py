# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import base64
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch


class VfDocumentTemplate(models.Model):
    _name = 'vf.document.template'
    _description = 'Document Template'
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
        domain="[('template_type', '=', 'document')]",
        tracking=True
    )
    
    # Template type
    template_type = fields.Selection([
        ('pdf_report', 'PDF Report'),
        ('certificate', 'Certificate'),
        ('form', 'Form Template'),
        ('letter', 'Letter Template'),
        ('contract', 'Contract Template'),
    ], string='Template Type', required=True, default='pdf_report')
    
    # Content
    body_html = fields.Html(
        string='HTML Content',
        help='HTML template for generating documents'
    )
    body_text = fields.Text(
        string='Text Content',
        help='Plain text template for simple documents'
    )
    
    # PDF template settings
    pdf_margin_top = fields.Float(
        string='Top Margin (inches)',
        default=0.75
    )
    pdf_margin_bottom = fields.Float(
        string='Bottom Margin (inches)',
        default=0.75
    )
    pdf_margin_left = fields.Float(
        string='Left Margin (inches)',
        default=0.75
    )
    pdf_margin_right = fields.Float(
        string='Right Margin (inches)',
        default=0.75
    )
    pdf_font_size = fields.Integer(
        string='Default Font Size',
        default=12
    )
    
    # Variables and dynamic content
    variable_ids = fields.One2many(
        'vf.template.variable',
        'template_id',
        string='Variables'
    )
    
    # Sample data for preview
    sample_data = fields.Text(
        string='Sample Data (JSON)',
        help='Sample data in JSON format for template preview'
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    # Preview
    preview_attachment_id = fields.Many2one(
        'ir.attachment',
        string='Preview',
        readonly=True
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

    def action_generate_preview(self):
        """Generate a preview of the template"""
        self.ensure_one()
        
        # Get sample data or use default
        sample_data = {}
        if self.sample_data:
            try:
                import json
                sample_data = json.loads(self.sample_data)
            except:
                pass
        
        # Default sample data
        if not sample_data:
            sample_data = {
                'member_name': 'John Doe',
                'membership_number': 'VF000001',
                'date': fields.Date.today().strftime('%d/%m/%Y'),
                'association_name': 'Vertical Association',
            }
        
        # Generate document based on type
        if self.template_type in ['pdf_report', 'certificate', 'letter']:
            attachment = self._generate_pdf_preview(sample_data)
        else:
            attachment = self._generate_html_preview(sample_data)
        
        self.preview_attachment_id = attachment.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Template Preview',
            'res_model': 'ir.attachment',
            'res_id': attachment.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _generate_pdf_preview(self, data):
        """Generate PDF preview"""
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Set margins
        width, height = letter
        left_margin = self.pdf_margin_left * inch
        right_margin = width - (self.pdf_margin_right * inch)
        top_margin = height - (self.pdf_margin_top * inch)
        bottom_margin = self.pdf_margin_bottom * inch
        
        # Draw content
        y_position = top_margin
        p.setFont("Helvetica", self.pdf_font_size)
        
        # Simple text rendering
        if self.body_text:
            lines = self.body_text.split('\n')
            for line in lines:
                # Replace variables
                for key, value in data.items():
                    line = line.replace(f'{{{{{key}}}}}', str(value))
                
                # Draw line
                if y_position > bottom_margin:
                    p.drawString(left_margin, y_position, line)
                    y_position -= (self.pdf_font_size * 1.2)
                else:
                    p.showPage()
                    y_position = top_margin
                    p.drawString(left_margin, y_position, line)
                    y_position -= (self.pdf_font_size * 1.2)
        
        p.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}_preview.pdf',
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return attachment

    def _generate_html_preview(self, data):
        """Generate HTML preview"""
        html_content = self.body_html or '<p>No content</p>'
        
        # Replace variables
        for key, value in data.items():
            html_content = html_content.replace(f'{{{{{key}}}}}', str(value))
        
        # Convert to PDF using webkit report
        try:
            from odoo.tools import pdf_utils
            pdf_content = pdf_utils.pdf_render(html_content)
            
            attachment = self.env['ir.attachment'].create({
                'name': f'{self.name}_preview.pdf',
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': self._name,
                'res_id': self.id,
            })
            
            return attachment
        except:
            # Fallback to HTML attachment
            attachment = self.env['ir.attachment'].create({
                'name': f'{self.name}_preview.html',
                'type': 'binary',
                'datas': base64.b64encode(html_content.encode()),
                'res_model': self._name,
                'res_id': self.id,
            })
            
            return attachment

    def action_create_document(self):
        """Create a new document from this template"""
        self.ensure_one()
        
        return {
            'name': _('Create Document from Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.document',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_name': _('New: %s') % self.name,
                'default_template_id': self.id,
                'default_category_id': self.env.ref('vf_document.category_general').id if self.env.ref('vf_document.category_general', False) else False,
            },
        }

    def action_test_variables(self):
        """Test template variables"""
        self.ensure_one()
        
        # Extract variables from template content
        variables = set()
        if self.body_html:
            import re
            variables.update(re.findall(r'\{\{(\w+)\}\}', self.body_html))
        if self.body_text:
            import re
            variables.update(re.findall(r'\{\{(\w+)\}\}', self.body_text))
        
        # Show found variables
        if variables:
            message = _('Found variables: %s') % ', '.join(sorted(variables))
        else:
            message = _('No variables found in template')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Variable Test'),
                'message': message,
                'type': 'info',
            }
        }
