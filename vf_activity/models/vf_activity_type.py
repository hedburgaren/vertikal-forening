# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfActivityType(models.Model):
    _name = 'vf.activity.type'
    _description = 'Activity Type'
    _order = 'sequence, name'

    # Core fields
    name = fields.Char(
        string='Activity Type',
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
    default_duration = fields.Float(
        string='Default Duration (hours)',
        default=1.0,
        help='Default duration for activities of this type'
    )
    allow_registration = fields.Boolean(
        string='Allow Registration',
        default=True,
        help='Members can register for activities of this type'
    )
    require_approval = fields.Boolean(
        string='Require Approval',
        default=False,
        help='Registration requires approval'
    )
    max_participants = fields.Integer(
        string='Maximum Participants',
        help='Default maximum number of participants'
    )
    
    # Categorization
    category = fields.Selection([
        ('sports', 'Sports'),
        ('training', 'Training'),
        ('social', 'Social'),
        ('meeting', 'Meeting'),
        ('competition', 'Competition'),
        ('camp', 'Camp'),
        ('other', 'Other'),
    ], string='Category', default='other', required=True)
    
    # Color for calendar
    color = fields.Integer(
        string='Color',
        default=0,
        help='Color index for calendar display'
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]
