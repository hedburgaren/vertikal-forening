# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfTemplateVariable(models.Model):
    _name = 'vf.template.variable'
    _description = 'Template Variable'
    _order = 'name'

    name = fields.Char(
        string='Variable Name',
        required=True,
        help='Variable name without double braces, e.g., member_name'
    )
    description = fields.Text(
        string='Description',
        help='Description of what this variable represents'
    )
    variable_type = fields.Selection([
        ('string', 'Text'),
        ('integer', 'Integer'),
        ('float', 'Decimal'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
        ('boolean', 'True/False'),
        ('html', 'HTML Content'),
        ('image', 'Image'),
    ], string='Type', required=True, default='string')
    
    # Relationships
    template_id = fields.Many2one(
        'vf.document.template',
        string='Document Template',
        ondelete='cascade'
    )
    email_template_id = fields.Many2one(
        'vf.email.template',
        string='Email Template',
        ondelete='cascade'
    )
    layout_id = fields.Many2one(
        'vf.communication.layout',
        string='Layout',
        ondelete='cascade'
    )
    
    # Default values
    default_value = fields.Text(
        string='Default Value',
        help='Default value for this variable'
    )
    example_value = fields.Text(
        string='Example Value',
        help='Example value for documentation'
    )
    
    # Validation
    required = fields.Boolean(
        string='Required',
        default=False
    )
    validation_regex = fields.Char(
        string='Validation Regex',
        help='Regular expression for validation'
    )
    
    _sql_constraints = [
        ('name_unique_template', 'unique(name, template_id)', 
         'Variable name must be unique within template!'),
        ('name_unique_email', 'unique(name, email_template_id)', 
         'Variable name must be unique within template!'),
        ('name_unique_layout', 'unique(name, layout_id)', 
         'Variable name must be unique within layout!'),
    ]

    @api.constrains('name')
    def _check_name_format(self):
        for variable in self:
            if variable.name and not variable.name.isidentifier():
                raise ValidationError(_(
                    'Variable name must be a valid identifier (letters, numbers, and underscore only)'
                ))
