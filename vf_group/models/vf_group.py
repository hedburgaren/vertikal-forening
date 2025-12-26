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
        default=lambda self: self.env.ref('vf_group.group_type_team').id
    )
    
    # Hierarchy
    parent_group_id = fields.Many2one(
        'vf.group',
        string='Parent Group',
        tracking=True,
        domain="[('section_id', '=', section_id)]"
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
        help='Maximum number of members allowed in this group'
    )
    min_age = fields.Integer(
        string='Minimum Age',
        tracking=True,
        help='Minimum age requirement for group members'
    )
    max_age = fields.Integer(
        string='Maximum Age',
        tracking=True,
        help='Maximum age requirement for group members'
    )
    
    # Management
    leader_id = fields.Many2one(
        'res.partner',
        string='Group Leader',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Statistics
    member_count = fields.Integer(
        string='Member Count',
        compute='_compute_member_count',
        store=True
    )
    active_member_count = fields.Integer(
        string='Active Member Count',
        compute='_compute_active_member_count',
        store=True
    )
    
    # Status
    is_active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    # Relationships
    member_ids = fields.One2many(
        'vf.group.membership',
        'group_id',
        string='Members'
    )
    position_ids = fields.One2many(
        'vf.position',
        'group_id',
        string='Positions'
    )

    @api.depends('name', 'section_id', 'code')
    def _compute_display_name(self):
        for group in self:
            parts = []
            if group.section_id:
                parts.append(group.section_id.name)
            if group.code:
                parts.append(f'[{group.code}]')
            parts.append(group.name)
            group.display_name = ' - '.join(parts)

    @api.depends('member_ids')
    def _compute_member_count(self):
        for group in self:
            group.member_count = len(group.member_ids)

    @api.depends('member_ids.is_active')
    def _compute_active_member_count(self):
        for group in self:
            group.active_member_count = len(group.member_ids.filtered('is_active'))

    @api.constrains('parent_group_id')
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive groups.'))

    @api.constrains('min_age', 'max_age')
    def _check_age_range(self):
        for group in self:
            if group.min_age and group.max_age and group.min_age > group.max_age:
                raise ValidationError(_('Minimum age cannot be greater than maximum age.'))

    @api.constrains('max_members')
    def _check_max_members(self):
        for group in self:
            if group.max_members and group.max_members < 1:
                raise ValidationError(_('Maximum members must be at least 1.'))

    @api.constrains('parent_group_id')
    def _check_parent_section(self):
        for group in self:
            if group.parent_group_id and group.parent_group_id.section_id != group.section_id:
                raise ValidationError(_('Parent group must be in the same section.'))

    def action_view_members(self):
        """Open member view with this group's members"""
        self.ensure_one()
        action = self.env.ref('vf_member.vf_member_action').read()[0]
        if self.member_ids:
            action['domain'] = [('id', 'in', self.member_ids.mapped('member_id').ids)]
        else:
            action['domain'] = [('id', '=', False)]
        action['context'] = {
            'default_group_id': self.id,
            'form_view_initial_mode': 'edit',
        }
        return action

    def action_add_members(self):
        """Open wizard to add members to group"""
        self.ensure_one()
        return {
            'name': _('Add Members to Group'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.group.membership.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_group_id': self.id},
        }

    def check_age_eligibility(self, member):
        """Check if a member is eligible for the group based on age"""
        if not self.min_age and not self.max_age:
            return True
        
        if member.age:
            if self.min_age and member.age < self.min_age:
                return False
            if self.max_age and member.age > self.max_age:
                return False
        
        return True

    def check_capacity(self):
        """Check if group has capacity for more members"""
        if not self.max_members:
            return True
        return self.active_member_count < self.max_members
