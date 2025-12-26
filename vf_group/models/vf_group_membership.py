# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class VfGroupMembership(models.Model):
    _name = 'vf.group.membership'
    _description = 'Group Membership'
    _order = 'group_id, member_id'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    group_id = fields.Many2one(
        'vf.group',
        string='Group',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Time management
    join_date = fields.Date(
        string='Join Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    leave_date = fields.Date(
        string='Leave Date',
        tracking=True,
        help='Date when member left the group'
    )
    
    # Status
    is_active = fields.Boolean(
        string='Active',
        compute='_compute_is_active',
        store=True,
        tracking=True
    )
    
    # Role in group (separate from vf.mandate)
    group_role = fields.Char(
        string='Group Role',
        tracking=True,
        help='Informal role or position within the group'
    )
    
    # Administrative
    notes = fields.Text(
        string='Notes',
        tracking=True,
        groups='vf_base.vf_admin'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_member_group', 
         'UNIQUE(member_id, group_id, join_date, leave_date)', 
         'A member can only have one membership in a group for the same period!'),
    ]

    @api.depends('join_date', 'leave_date')
    def _compute_is_active(self):
        today = date.today()
        for membership in self:
            if membership.leave_date:
                membership.is_active = membership.join_date <= today <= membership.leave_date
            else:
                membership.is_active = membership.join_date <= today

    @api.depends('member_id', 'group_id')
    def _compute_display_name(self):
        for membership in self:
            membership.display_name = f'{membership.member_id.partner_id.name} - {membership.group_id.name}'

    @api.constrains('join_date', 'leave_date')
    def _check_dates(self):
        for membership in self:
            if membership.leave_date and membership.join_date > membership.leave_date:
                raise ValidationError(_('Join date must be before leave date.'))

    @api.constrains('member_id', 'group_id')
    def _check_age_eligibility(self):
        """Check if member meets age requirements"""
        for membership in self:
            if membership.group_id.min_age or membership.group_id.max_age:
                if not membership.group_id.check_age_eligibility(membership.member_id):
                    raise ValidationError(_(
                        'Member does not meet age requirements for this group. '
                        'Group age range: %s - %s'
                    ) % (
                        membership.group_id.min_age or _('No minimum'),
                        membership.group_id.max_age or _('No maximum')
                    ))

    @api.constrains('group_id')
    def _check_capacity(self):
        """Check if group has capacity for new members"""
        for membership in self:
            if membership.join_date <= date.today() and not membership.leave_date:
                if not membership.group_id.check_capacity():
                    raise ValidationError(_('Group has reached maximum capacity.'))

    def action_leave_group(self, leave_date=None):
        """End the group membership"""
        if not leave_date:
            leave_date = date.today()
        self.write({'leave_date': leave_date})
        return True

    def action_reactivate(self):
        """Reactivate a membership"""
        self.write({'leave_date': False})
        return True

    @api.model
    def get_active_members(self, group_id):
        """Get all active members for a group"""
        return self.search([
            ('group_id', '=', group_id),
            ('is_active', '=', True)
        ])

    @api.model
    def get_member_groups(self, member_id, active_only=True):
        """Get all groups for a member"""
        domain = [('member_id', '=', member_id)]
        if active_only:
            domain.append(('is_active', '=', True))
        return self.search(domain)
