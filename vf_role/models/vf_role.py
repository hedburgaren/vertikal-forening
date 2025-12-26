# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfRole(models.Model):
    _name = 'vf.role'
    _description = 'Association Role'
    _order = 'sequence, name'

    # Core fields
    name = fields.Char(
        string='Role Name',
        required=True,
        translate=True
    )
    code = fields.Char(
        string='Role Code',
        required=True,
        help='Unique code for programmatic reference'
    )
    description = fields.Html(
        string='Description',
        translate=True
    )
    
    # Access level
    access_level = fields.Selection([
        ('organization', 'Organization Level'),
        ('section', 'Section Level'),
        ('group', 'Group Level'),
    ], string='Access Level', required=True, default='group')
    
    # Configuration
    is_managerial = fields.Boolean(
        string='Managerial Role',
        help='Can assign other roles and manage resources'
    )
    requires_approval = fields.Boolean(
        string='Requires Approval',
        help='This role needs board approval before assignment'
    )
    
    # System integration
    group_ids = fields.Many2many(
        'res.groups',
        'vf_role_group_rel',
        'role_id',
        'group_id',
        string='Odoo Groups',
        help='Odoo user groups that get this role automatically'
    )
    
    # Status
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    active = fields.Boolean(
        default=True
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]
