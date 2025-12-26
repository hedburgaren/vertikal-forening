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
        tracking=True,
        help='HTML content for the template'
    )
    body_text = fields.Text(
        string='Text Content',
        tracking=True,
        help='Plain text content for the template'
    )
    
    # PDF layout settings
    pdf_layout = fields.Selection([
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ], string='PDF Layout', default='portrait')
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
    
    # Variables and sample data
    variable_ids = fields.Many2many(
        'vf.template.variable',
        'vf_document_template_variable_rel',
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
    document_count = fields.Integer(
        string='Documents Created',
        compute='_compute_document_count',
        store=True
    )

    @api.depends('name', 'category_id')
    def _compute_display_name(self):
        for template in self:
            if template.category_id:
                template.display_name = f'{template.category_id.name} / {template.name}'
            else:
                template.display_name = template.name

    @api.depends('generated_document_ids')
    def _compute_document_count(self):
        for template in self:
            template.document_count = len(template.generated_document_ids)

    def action_preview(self):
        """Preview the template with sample data"""
        self.ensure_one()
        return {
            'name': _('Preview Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.template.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_template_model': 'vf.document.template',
            },
        }

    def action_create_document(self):
        """Create a document from this template"""
        self.ensure_one()
        return {
            'name': _('Create Document'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.template.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_template_model': 'vf.document.template',
            },
        }

    def generate_pdf(self, data):
        """Generate PDF from template"""
        self.ensure_one()
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Create PDF
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Apply margins
        margin_left = self.pdf_margin_left * inch
        margin_right = self.pdf_margin_right * inch
        margin_top = self.pdf_margin_top * inch
        margin_bottom = self.pdf_margin_bottom * inch
        
        # Draw content
        text_width = width - margin_left - margin_right
        text_height = height - margin_top - margin_bottom
        
        # Simple text rendering - in practice, you'd use a proper
        # HTML to PDF converter like WeasyPrint
        if self.body_text:
            y_position = height - margin_top
            for line in self.body_text.split('\n'):
                p.drawString(margin_left, y_position, line)
                y_position -= 12
        
        p.save()
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return base64.b64encode(pdf_content)

    def get_variables(self):
        """Get all variables used in this template"""
        variables = []
        if self.body_html:
            # Extract variables from HTML
            import re
            pattern = r'\{\{([^}]+)\}\}'
            matches = re.findall(pattern, self.body_html)
            variables.extend(matches)
        
        if self.body_text:
            pattern = r'\{\{([^}]+)\}\}'
            matches = re.findall(pattern, self.body_text)
            variables.extend(matches)
        
        # Return unique variables
        return list(set(variables))
