# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfRelationshipType(models.Model):
    _name = 'vf.relationship.type'
    _description = 'Relationship Type'
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
    
    # Usage context
    is_guardian_type = fields.Boolean(
        string='Guardian Relationship',
        help='This type can be used for guardian relationships'
    )
    is_family_type = fields.Boolean(
        string='Family Relationship',
        help='This type can be used for family relationships'
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]
