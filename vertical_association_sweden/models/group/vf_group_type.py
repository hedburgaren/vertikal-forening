# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfGroupType(models.Model):
    _name = 'vf.group.type'
    _description = 'Group Type'
    _order = 'sequence, code'

    # Core fields
    name = fields.Char(
        string='Name',
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
    
    # Default settings
    default_max_members = fields.Integer(
        string='Default Maximum Members',
        help='Default maximum members for groups of this type'
    )
    default_min_age = fields.Integer(
        string='Default Minimum Age',
        help='Default minimum age for groups of this type'
    )
    default_max_age = fields.Integer(
        string='Default Maximum Age',
        help='Default maximum age for groups of this type'
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]
