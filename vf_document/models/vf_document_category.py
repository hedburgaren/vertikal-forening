# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfDocumentCategory(models.Model):
    _name = 'vf.document.category'
    _description = 'Document Category'
    _order = 'sequence, name'

    # Core fields
    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True
    )
    code = fields.Char(
        string='Code',
        required=True,
        help='Unique code for programmatic reference'
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    # Configuration
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    active = fields.Boolean(
        default=True
    )
    
    # Default visibility
    default_visibility = fields.Selection([
        ('public', 'Public'),
        ('members', 'Members Only'),
        ('leadership', 'Leadership Only'),
        ('custom', 'Custom'),
    ], string='Default Visibility', default='members', required=True)
    
    # Template settings
    allow_templates = fields.Boolean(
        string='Allow Templates',
        default=True,
        help='Allow creating document templates in this category'
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]
