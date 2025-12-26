# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfSection(models.Model):
    _name = 'vf.section'
    _description = 'Association Section'
    _order = 'name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Section Name',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Section Code',
        tracking=True,
        help='Short code for identification'
    )
    description = fields.Html(
        string='Description',
        tracking=True
    )
    
    # Hierarchy
    parent_id = fields.Many2one(
        'vf.section',
        string='Parent Section',
        tracking=True
    )
    child_ids = fields.One2many(
        'vf.section',
        'parent_id',
        string='Child Sections'
    )
    
    # Management
    manager_id = fields.Many2one(
        'res.partner',
        string='Section Manager',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Statistics
    group_count = fields.Integer(
        string='Group Count',
        compute='_compute_group_count',
        store=True
    )
    member_count = fields.Integer(
        string='Member Count',
        compute='_compute_member_count',
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
    level = fields.Integer(
        compute='_compute_level',
        store=True
    )

    @api.depends('name', 'code')
    def _compute_display_name(self):
        for section in self:
            if section.code:
                section.display_name = f'[{section.code}] {section.name}'
            else:
                section.display_name = section.name

    @api.depends('parent_id')
    def _compute_level(self):
        for section in self:
            if section.parent_id:
                section.level = section.parent_id.level + 1
            else:
                section.level = 0

    @api.depends('group_ids')
    def _compute_group_count(self):
        for section in self:
            section.group_count = len(section.group_ids)

    @api.depends('group_ids.member_ids')
    def _compute_member_count(self):
        for section in self:
            # Count unique members across all groups
            members = section.group_ids.mapped('member_ids')
            section.member_count = len(members)

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error! You cannot create recursive sections.'))

    def action_view_groups(self):
        """Open group view with this section's groups"""
        self.ensure_one()
        action = self.env.ref('vf_group.vf_group_action').read()[0]
        action['domain'] = [('section_id', '=', self.id)]
        action['context'] = {'default_section_id': self.id}
        return action

    def action_view_members(self):
        """Open member view with this section's members"""
        self.ensure_one()
        members = self.group_ids.mapped('member_ids')
        action = self.env.ref('vf_member.vf_member_action').read()[0]
        if members:
            action['domain'] = [('id', 'in', members.ids)]
        else:
            action['domain'] = [('id', '=', False)]
        return action

    def name_get(self):
        """Display section hierarchy in name"""
        result = []
        for section in self:
            name = section.display_name
            if section.level > 0:
                name = '  ' * section.level + name
            result.append((section.id, name))
        return result
