# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfGroup(models.Model):
    _name = 'vf.group'
    _description = 'Association Group'
    _order = 'section_id, name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Group Name',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Group Code',
        tracking=True,
        help='Short code for identification'
    )
    description = fields.Html(
        string='Description',
        tracking=True
    )
    
    # Organization
    section_id = fields.Many2one(
        'vf.section',
        string='Section',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    group_type_id = fields.Many2one(
        'vf.group.type',
        string='Group Type',
        required=True,
        tracking=True,
        default=lambda self: self.env.ref('vertical_association_sweden.group_type_team').id
    )
    
    # Hierarchy
    parent_group_id = fields.Many2one(
        'vf.group',
        string='Parent Group',
        tracking=True
    )
    child_group_ids = fields.One2many(
        'vf.group',
        'parent_group_id',
        string='Child Groups'
    )
    
    # Capacity and restrictions
    max_members = fields.Integer(
        string='Maximum Members',
        tracking=True,
        help='Maximum number of members in this group'
    )
    min_age = fields.Integer(
        string='Minimum Age',
        tracking=True
    )
    max_age = fields.Integer(
        string='Maximum Age',
        tracking=True
    )
    
    # Member relationships
    member_ids = fields.One2many(
        'vf.group.membership',
        'group_id',
        string='Members',
        tracking=True
    )
    member_count = fields.Integer(
        string='Member Count',
        compute='_compute_member_count',
        store=True
    )
    active_member_count = fields.Integer(
        string='Active Members',
        compute='_compute_active_member_count',
        store=True
    )
    
    # Leadership
    leader_ids = fields.One2many(
        'vf.group.leadership',
        'group_id',
        string='Leaders'
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
    
    # Constraints
    _sql_constraints = [
        ('code_section_unique', 'unique(code, section_id)', 'Group code must be unique within section!'),
        ('name_section_unique', 'unique(name, section_id)', 'Group name must be unique within section!'),
    ]

    @api.depends('name', 'section_id')
    def _compute_display_name(self):
        for group in self:
            if group.section_id:
                group.display_name = f'{group.section_id.name} - {group.name}'
            else:
                group.display_name = group.name

    @api.depends('member_ids')
    def _compute_member_count(self):
        for group in self:
            group.member_count = len(group.member_ids)

    @api.depends('member_ids.is_active')
    def _compute_active_member_count(self):
        for group in self:
            group.active_member_count = len(group.member_ids.filtered('is_active'))

    @api.constrains('min_age', 'max_age')
    def _check_age_range(self):
        for group in self:
            if group.min_age and group.max_age and group.min_age > group.max_age:
                raise ValidationError(_('Minimum age cannot be greater than maximum age.'))

    @api.constrains('parent_group_id')
    def _check_hierarchy(self):
        for group in self:
            if group.parent_group_id:
                # Check for circular reference
                parent = group.parent_group_id
                while parent:
                    if parent == group:
                        raise ValidationError(_('Circular reference detected in group hierarchy.'))
                    parent = parent.parent_group_id

    def action_view_members(self):
        """Open member view with this group's members"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_group_membership_action').read()[0]
        action['domain'] = [('group_id', '=', self.id)]
        action['context'] = {'default_group_id': self.id}
        return action

    def action_add_members(self):
        """Open wizard to add members"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Add Members',
            'res_model': 'vf.group.membership',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_group_id': self.id},
        }

    def action_view_leaders(self):
        """Open leadership view"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_group_leadership_action').read()[0]
        action['domain'] = [('group_id', '=', self.id)]
        action['context'] = {'default_group_id': self.id}
        return action

    def has_capacity(self):
        """Check if group has capacity for more members"""
        if not self.max_members:
            return True
        return self.active_member_count < self.max_members

    def get_age_compatible_members(self):
        """Get members that are within the age range"""
        domain = []
        if self.min_age:
            domain.append(('age', '>=', self.min_age))
        if self.max_age:
            domain.append(('age', '<=', self.max_age))
        return self.env['vf.member'].search(domain) if domain else self.env['vf.member']

    @api.model
    def get_groups_for_member(self, member_id):
        """Get all groups a member can join based on age and capacity"""
        member = self.env['vf.member'].browse(member_id)
        groups = self.search([
            ('active', '=', True),
        ])
        
        compatible_groups = self.env['vf.group']
        for group in groups:
            if group.has_capacity():
                if not group.min_age or member.age >= group.min_age:
                    if not group.max_age or member.age <= group.max_age:
                        compatible_groups |= group
        
        return compatible_groups
