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
    email_body_bg_color = fields.Char(
        string='Email Background Color',
        default='#ffffff',
        tracking=True
    )
    email_container_bg_color = fields.Char(
        string='Container Background Color',
        default='#f8f9fa',
        tracking=True
    )
    email_text_color = fields.Char(
        string='Text Color',
        default='#333333',
        tracking=True
    )
    email_link_color = fields.Char(
        string='Link Color',
        default='#007bff',
        tracking=True
    )
    
    # Letter specific settings
    letter_header_height = fields.Float(
        string='Header Height (cm)',
        default=3.0
    )
    letter_footer_height = fields.Float(
        string='Footer Height (cm)',
        default=2.0
    )
    letter_margin = fields.Float(
        string='Page Margin (cm)',
        default=2.0
    )
    
    # Branding
    logo_id = fields.Many2one(
        'ir.attachment',
        string='Logo',
        tracking=True
    )
    brand_color = fields.Char(
        string='Brand Color',
        default='#0056b3',
        tracking=True
    )
    
    # Variables and sample data
    variable_ids = fields.Many2many(
        'vf.template.variable',
        'vf_communication_layout_variable_rel',
        'layout_id',
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
    is_default = fields.Boolean(
        string='Default Layout',
        help='Use as default layout for this type'
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
    
    # Preview
    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview_html'
    )

    @api.depends('name', 'category_id')
    def _compute_display_name(self):
        for layout in self:
            if layout.category_id:
                layout.display_name = f'{layout.category_id.name} / {layout.name}'
            else:
                layout.display_name = layout.name

    @api.depends('used_in_emails', 'used_in_documents')
    def _compute_usage_count(self):
        for layout in self:
            layout.usage_count = (
                len(layout.used_in_emails) + 
                len(layout.used_in_documents)
            )

    @api.depends('header_html', 'footer_html', 'layout_type')
    def _compute_preview_html(self):
        for layout in self:
            if layout.layout_type == 'email':
                layout.preview_html = self._generate_email_preview(layout)
            else:
                layout.preview_html = False

    @api.constrains('is_default')
    def _check_unique_default(self):
        """Only one default layout per type"""
        for layout in self:
            if layout.is_default:
                other = self.search([
                    ('layout_type', '=', layout.layout_type),
                    ('is_default', '=', True),
                    ('id', '!=', layout.id)
                ])
                if other:
                    raise ValidationError(_('Only one default layout is allowed per type.'))

    def action_preview(self):
        """Preview the layout"""
        self.ensure_one()
        return {
            'name': _('Preview Layout'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.template.preview.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_template_model': 'vf.communication.layout',
            },
        }

    def action_set_default(self):
        """Set this layout as default"""
        self.ensure_one()
        
        # Clear other defaults
        self.search([
            ('layout_type', '=', self.layout_type),
            ('is_default', '=', True)
        ]).write({'is_default': False})
        
        # Set this as default
        self.write({'is_default': True})
        
        return True

    def _generate_email_preview(self, layout):
        """Generate email preview HTML"""
        header = layout.header_html or ''
        footer = layout.footer_html or ''
        
        sample_content = '''
        <div style="padding: 20px; font-family: Arial, sans-serif;">
            <h2>Sample Content</h2>
            <p>This is a preview of how your email will look with this layout.</p>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit.</p>
        </div>
        '''
        
        return f'''
        <div style="background-color: {layout.email_body_bg_color}; padding: 20px;">
            <div style="background-color: {layout.email_container_bg_color}; max-width: 600px; margin: 0 auto;">
                {header}
                {sample_content}
                {footer}
            </div>
        </div>
        '''

    def apply_layout(self, content, context=None):
        """Apply layout to content"""
        self.ensure_one()
        
        if not context:
            context = {}
        
        # Render header and footer with context
        header = self._render_template(self.header_html or '', context)
        footer = self._render_template(self.footer_html or '', context)
        
        if self.layout_type == 'email':
            return self._apply_email_layout(header, content, footer)
        elif self.layout_type == 'letter':
            return self._apply_letter_layout(header, content, footer)
        else:
            return header + content + footer

    def _apply_email_layout(self, header, content, footer):
        """Apply email-specific layout"""
        return f'''
        <div style="background-color: {self.email_body_bg_color}; padding: 20px;">
            <div style="background-color: {self.email_container_bg_color}; max-width: 600px; margin: 0 auto;">
                {header}
                <div style="color: {self.email_text_color};">
                    {content}
                </div>
                {footer}
            </div>
        </div>
        '''

    def _apply_letter_layout(self, header, content, footer):
        """Apply letter-specific layout"""
        return f'''
        <div style="margin: {self.letter_margin}cm;">
            {header}
            <div style="min-height: calc(100% - {self.letter_header_height + self.letter_footer_height}cm);">
                {content}
            </div>
            {footer}
        </div>
        '''

    def _render_template(self, template, context):
        """Render template with context variables"""
        try:
            # Simple rendering - in practice, you'd use proper Jinja2
            return template
        except Exception:
            return template

    def get_variables(self):
        """Get all variables used in this layout"""
        variables = []
        
        # Extract from header
        import re
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, self.header_html or '')
        variables.extend(matches)
        
        # Extract from footer
        matches = re.findall(pattern, self.footer_html or '')
        variables.extend(matches)
        
        # Return unique variables
        return list(set(variables))
