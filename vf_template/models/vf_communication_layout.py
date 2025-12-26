# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfCommunicationLayout(models.Model):
    _name = 'vf.communication.layout'
    _description = 'Communication Layout'
    _order = 'category_id, name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Layout Name',
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
        domain="[('template_type', '=', 'layout')]",
        tracking=True
    )
    
    # Layout type
    layout_type = fields.Selection([
        ('email', 'Email Layout'),
        ('letter', 'Letter Template'),
        ('export_pdf', 'PDF Export'),
        ('export_excel', 'Excel Export'),
        ('report', 'Report Layout'),
    ], string='Layout Type', required=True, default='email')
    
    # Header and footer
    header_html = fields.Html(
        string='Header HTML',
        help='Header content for the layout'
    )
    footer_html = fields.Html(
        string='Footer HTML',
        help='Footer content for the layout'
    )
    
    # Email specific settings
    email_body_style = fields.Text(
        string='Body CSS Styles',
        help='CSS styles for email body'
    )
    email_wrapper_style = fields.Text(
        string='Wrapper CSS Styles',
        help='CSS styles for email wrapper/container'
    )
    
    # Letter specific settings
    letter_header_margin = fields.Float(
        string='Header Margin (cm)',
        default=2.0
    )
    letter_footer_margin = fields.Float(
        string='Footer Margin (cm)',
        default=2.0
    )
    letter_body_margin = fields.Float(
        string='Body Margin (cm)',
        default=2.5
    )
    letter_font_family = fields.Char(
        string='Font Family',
        default='Times New Roman'
    )
    letter_font_size = fields.Integer(
        string='Font Size (pt)',
        default=12
    )
    
    # Export settings
    export_orientation = fields.Selection([
        ('portrait', 'Portrait'),
        ('landscape', 'Landscape'),
    ], string='Page Orientation', default='portrait')
    
    # Brand customization
    primary_color = fields.Char(
        string='Primary Color',
        default='#003366'
    )
    secondary_color = fields.Char(
        string='Secondary Color',
        default='#666666'
    )
    accent_color = fields.Char(
        string='Accent Color',
        default='#ff6600'
    )
    background_color = fields.Char(
        string='Background Color',
        default='#ffffff'
    )
    
    # Logo settings
    logo_id = fields.Many2one(
        'ir.attachment',
        string='Logo',
        domain="[('res_field', '=', False), ('res_model', '=', False)]"
    )
    logo_max_width = fields.Integer(
        string='Logo Max Width (px)',
        default=200
    )
    logo_max_height = fields.Integer(
        string='Logo Max Height (px)',
        default=100
    )
    
    # Variables
    variable_ids = fields.One2many(
        'vf.template.variable',
        'layout_id',
        string='Variables'
    )
    
    # Preview
    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview_html'
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    is_default = fields.Boolean(
        string='Default Layout',
        help='Make this the default layout for its type'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    _sql_constraints = [
        ('name_unique_category', 'unique(name, category_id)', 
         'Layout name must be unique within category!'),
        ('unique_default_type', 'unique(is_default, layout_type)', 
         'Only one default layout allowed per type!'),
    ]

    @api.depends('name', 'category_id')
    def _compute_display_name(self):
        for layout in self:
            if layout.category_id:
                layout.display_name = f'{layout.category_id.name} / {layout.name}'
            else:
                layout.display_name = layout.name

    @api.depends('header_html', 'footer_html', 'layout_type')
    def _compute_preview_html(self):
        for layout in self:
            if layout.layout_type == 'email':
                layout.preview_html = layout._generate_email_preview()
            elif layout.layout_type == 'letter':
                layout.preview_html = layout._generate_letter_preview()
            else:
                layout.preview_html = '<p>Preview not available for this layout type</p>'

    def _generate_email_preview(self):
        """Generate email preview"""
        # Sample content
        sample_content = """
        <div style="font-family: Arial, sans-serif; color: #333;">
            <h1>Sample Email Content</h1>
            <p>This is a preview of your email layout.</p>
            <p>Dear {{member_name}},</p>
            <p>This is where your email content would appear.</p>
            <p>Best regards,<br>{{association_name}}</p>
        </div>
        """
        
        # Build complete email
        email_html = ""
        
        # Header
        if self.header_html:
            email_html += self.header_html
        
        # Wrapper with styles
        email_html += f'<div style="{self.email_wrapper_style or "max-width: 600px; margin: 0 auto;"}">'
        email_html += f'<div style="{self.email_body_style or "padding: 20px; background: white;"}">'
        email_html += sample_content
        email_html += '</div></div>'
        
        # Footer
        if self.footer_html:
            email_html += self.footer_html
        
        return email_html

    def _generate_letter_preview(self):
        """Generate letter preview"""
        # Sample content
        sample_content = """
        <div style="text-align: left; margin-bottom: 50px;">
            <p>{{date}}</p>
            <p>{{member_name}}<br>
            {{member_address}}<br>
            {{member_city}} {{member_zip}}</p>
        </div>
        
        <div style="margin-bottom: 50px;">
            <p>Dear {{member_name}},</p>
            <p>This is a preview of your letter layout.</p>
            <p>This is where your letter content would appear.</p>
        </div>
        
        <div style="text-align: right;">
            <p>Best regards,<br>
            {{association_name}}<br>
            {{association_address}}</p>
        </div>
        """
        
        return sample_content

    def action_preview(self):
        """Open preview window"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Layout Preview'),
            'res_model': 'vf.communication.layout',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(False, 'form')],
            'context': {'form_view_initial_mode': 'readonly'},
        }

    def action_test_layout(self):
        """Test layout with sample data"""
        self.ensure_one()
        
        if self.layout_type == 'email':
            # Create test email
            test_context = {
                'member_name': 'John Doe',
                'member_address': '123 Main Street',
                'member_city': 'Stockholm',
                'member_zip': '12345',
                'date': fields.Date.today().strftime('%d/%m/%Y'),
                'association_name': 'Vertical Association',
                'association_address': '456 Association Ave',
            }
            
            # Render layout
            rendered_html = self._render_layout(test_context)
            
            # Create preview
            preview = self.env['mail.compose.message'].create({
                'subject': 'Layout Test',
                'body': rendered_html,
                'composition_mode': 'comment',
                'model': self._name,
                'res_id': self.id,
            })
            
            return {
                'type': 'ir.actions.act_window',
                'name': _('Layout Test'),
                'res_model': 'mail.compose.message',
                'res_id': preview.id,
                'view_mode': 'form',
                'target': 'new',
            }
        
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Layout Test'),
                    'message': _('Test feature is available for email layouts only'),
                    'type': 'info',
                }
            }

    def _render_layout(self, context):
        """Render layout with context variables"""
        # Start with header
        html = self.header_html or ''
        
        # Add body wrapper
        if self.layout_type == 'email':
            html += f'<div style="{self.email_wrapper_style or ""}">'
            html += f'<div style="{self.email_body_style or ""}">'
        
        # Add sample body
        html += '<p>This is the body content with variables:</p>'
        for key, value in context.items():
            html += f'<p>{{{{{key}}}}} = {value}</p>'
        
        # Close wrappers
        if self.layout_type == 'email':
            html += '</div></div>'
        
        # Add footer
        html += self.footer_html or ''
        
        # Replace variables
        for key, value in context.items():
            html = html.replace(f'{{{{{key}}}}}', str(value))
        
        return html

    def action_set_as_default(self):
        """Set this layout as default for its type"""
        self.ensure_one()
        
        # Clear other defaults
        self.search([
            ('layout_type', '=', self.layout_type),
            ('is_default', '=', True)
        ]).write({'is_default': False})
        
        # Set this as default
        self.is_default = True
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Default Layout Set'),
                'message': _('This layout is now the default for %s') % dict(self._fields['layout_type'].selection).get(self.layout_type),
                'type': 'success',
            }
        }
