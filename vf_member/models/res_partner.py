# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Member relationship
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        readonly=True,
        copy=False
    )
    is_member = fields.Boolean(
        string='Is Member',
        compute='_compute_is_member',
        search='_search_is_member'
    )
    
    # Guardian relationships
    minor_guardian_ids = fields.One2many(
        'vf.guardian.relationship',
        'guardian_id',
        string='Guardian For'
    )
    has_guardian_responsibilities = fields.Boolean(
        compute='_compute_has_guardian_responsibilities'
    )
    
    # Household relationships
    household_member_ids = fields.One2many(
        'vf.member',
        compute='_compute_household_members',
        string='Household Members'
    )
    
    @api.depends('member_id')
    def _compute_is_member(self):
        for partner in self:
            partner.is_member = bool(partner.member_id)

    def _search_is_member(self, operator, value):
        """Search partners who are members"""
        if operator == '=' and value:
            return [('member_id', '!=', False)]
        elif operator == '=' and not value:
            return [('member_id', '=', False)]
        return []

    @api.depends('minor_guardian_ids.is_active')
    def _compute_has_guardian_responsibilities(self):
        for partner in self:
            partner.has_guardian_responsibilities = any(
                rel.is_active for rel in partner.minor_guardian_ids
            )

    def _compute_household_members(self):
        """Get all members in the same household"""
        for partner in self:
            if partner.member_id and partner.member_id.household_id:
                household = partner.member_id.household_id
                partner.household_member_ids = household.member_ids
            else:
                partner.household_member_ids = False

    def action_view_member(self):
        """Open the member record for this partner"""
        self.ensure_one()
        if self.member_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Member',
                'res_model': 'vf.member',
                'res_id': self.member_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def action_create_member(self):
        """Create a member record for this partner"""
        self.ensure_one()
        if not self.member_id:
            member = self.env['vf.member'].create({
                'partner_id': self.id,
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Member',
                'res_model': 'vf.member',
                'res_id': member.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return self.action_view_member()

    def action_view_guardian_relationships(self):
        """View all guardian relationships for this partner"""
        self.ensure_one()
        action = self.env.ref('vf_member.vf_guardian_relationship_action').read()[0]
        action['domain'] = [('guardian_id', '=', self.id)]
        return action

    def name_get(self):
        """Add member number to partner name if they are a member"""
        result = super().name_get()
        new_result = []
        for partner_id, name in result:
            partner = self.browse(partner_id)
            if partner.member_id and partner.member_id.membership_number:
                name = f'{name} ({partner.member_id.membership_number})'
            new_result.append((partner_id, name))
        return new_result
