# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Mandate relationships
    mandate_ids = fields.One2many(
        'vf.mandate',
        'person_id',
        string='Mandates'
    )
    active_mandate_ids = fields.One2many(
        'vf.mandate',
        compute='_compute_active_mandates',
        string='Active Mandates'
    )
    has_active_mandates = fields.Boolean(
        compute='_compute_has_active_mandates'
    )
    
    # Role information
    current_roles = fields.Text(
        compute='_compute_current_roles',
        string='Current Roles'
    )
    is_leader = fields.Boolean(
        compute='_compute_is_leader',
        search='_search_is_leader'
    )
    is_manager = fields.Boolean(
        compute='_compute_is_manager',
        search='_search_is_manager'
    )

    def _compute_active_mandates(self):
        for partner in self:
            partner.active_mandate_ids = partner.mandate_ids.filtered(
                lambda m: m.status == 'active'
            )

    def _compute_has_active_mandates(self):
        for partner in self:
            partner.has_active_mandates = bool(partner.active_mandate_ids)

    def _compute_current_roles(self):
        for partner in self:
            roles = []
            for mandate in partner.active_mandate_ids:
                if mandate.position_id.role_id.name not in roles:
                    roles.append(mandate.position_id.role_id.name)
            partner.current_roles = ', '.join(roles)

    def _compute_is_leader(self):
        for partner in self:
            partner.is_leader = any(
                mandate.position_id.role_id.access_level in ['section', 'group']
                for mandate in partner.active_mandate_ids
            )

    def _compute_is_manager(self):
        for partner in self:
            partner.is_manager = any(
                mandate.position_id.role_id.is_managerial
                for mandate in partner.active_mandate_ids
            )

    def _search_is_leader(self, operator, value):
        """Search partners with leadership roles"""
        if operator == '=' and value:
            return [('mandate_ids.status', '=', 'active'),
                    ('mandate_ids.position_id.role_id.access_level', 'in', ['section', 'group'])]
        elif operator == '=' and not value:
            return [('mandate_ids.status', '=', 'active'),
                    ('mandate_ids.position_id.role_id.access_level', 'not in', ['section', 'group'])]
        return []

    def _search_is_manager(self, operator, value):
        """Search partners with managerial roles"""
        if operator == '=' and value:
            return [('mandate_ids.status', '=', 'active'),
                    ('mandate_ids.position_id.role_id.is_managerial', '=', True)]
        elif operator == '=' and not value:
            return [('mandate_ids.status', '=', 'active'),
                    ('mandate_ids.position_id.role_id.is_managerial', '=', False)]
        return []

    def action_view_mandates(self):
        """View all mandates for this partner"""
        self.ensure_one()
        action = self.env.ref('vf_role.vf_mandate_action').read()[0]
        action['domain'] = [('person_id', '=', self.id)]
        return action

    def action_assign_mandate(self):
        """Assign a new mandate to this partner"""
        self.ensure_one()
        return {
            'name': 'Assign Mandate',
            'type': 'ir.actions.act_window',
            'res_model': 'vf.mandate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_person_id': self.id},
        }
