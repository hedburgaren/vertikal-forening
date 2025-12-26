# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfTemplateCategory(models.Model):
    _name = 'vf.template.category'
    _description = 'Template Category'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    template_type = fields.Selection([
        ('document', 'Document Template'),
        ('email', 'Email Template'),
        ('layout', 'Communication Layout'),
    ], string='Template Type', required=True)
    
    # Default visibility for document templates
    default_visibility = fields.Selection([
        ('public', 'Public'),
        ('members', 'Members Only'),
        ('leadership', 'Leadership Only'),
        ('custom', 'Custom'),
    ], string='Default Visibility', default='members')
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Statistics
    document_template_count = fields.Integer(
        string='Document Templates',
        compute='_compute_template_counts'
    )
    email_template_count = fields.Integer(
        string='Email Templates',
        compute='_compute_template_counts'
    )
    layout_count = fields.Integer(
        string='Layouts',
        compute='_compute_template_counts'
    )

    @api.depends('template_type')
    def _compute_template_counts(self):
        for category in self:
            category.document_template_count = 0
            category.email_template_count = 0
            category.layout_count = 0
            
            if category.template_type == 'document':
                category.document_template_count = self.env['vf.document.template'].search_count([
                    ('category_id', '=', category.id)
                ])
            elif category.template_type == 'email':
                category.email_template_count = self.env['vf.email.template'].search_count([
                    ('category_id', '=', category.id)
                ])
            elif category.template_type == 'layout':
                category.layout_count = self.env['vf.communication.layout'].search_count([
                    ('category_id', '=', category.id)
                ])
