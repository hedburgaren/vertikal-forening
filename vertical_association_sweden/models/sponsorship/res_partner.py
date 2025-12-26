# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Sponsorship related fields
    is_sponsor = fields.Boolean(
        string='Is Sponsor',
        help='Check if this partner is a sponsor'
    )
    sponsor_ids = fields.One2many(
        'vf.sponsor',
        'partner_id',
        string='Sponsorships'
    )
    current_sponsorship_id = fields.Many2one(
        'vf.sponsor',
        compute='_compute_current_sponsorship',
        string='Current Sponsorship'
    )
    sponsorship_level = fields.Char(
        compute='_compute_sponsorship_level',
        string='Sponsorship Level'
    )
    
    # Merchandise related
    merchandise_order_ids = fields.One2many(
        'vf.merchandise.order',
        'partner_id',
        string='Merchandise Orders'
    )
    merchandise_order_count = fields.Integer(
        compute='_compute_merchandise_count',
        string='Merchandise Orders'
    )
    
    # Quick actions
    has_active_contract = fields.Boolean(
        compute='_compute_has_active_contract',
        string='Has Active Contract'
    )

    @api.depends('sponsor_ids')
    def _compute_current_sponsorship(self):
        for partner in self:
            active_sponsor = partner.sponsor_ids.filtered(lambda s: s.state == 'active')
            partner.current_sponsorship_id = active_sponsor[:1] if active_sponsor else False

    @api.depends('current_sponsorship_id')
    def _compute_sponsorship_level(self):
        for partner in self:
            if partner.current_sponsorship_id:
                partner.sponsorship_level = partner.current_sponsorship_id.sponsorship_level_id.name
            else:
                partner.sponsorship_level = False

    @api.depends('merchandise_order_ids')
    def _compute_merchandise_count(self):
        for partner in self:
            partner.merchandise_order_count = len(partner.merchandise_order_ids)

    @api.depends('sponsor_ids.contract_ids')
    def _compute_has_active_contract(self):
        for partner in self:
            partner.has_active_contract = bool(
                partner.sponsor_ids.contract_ids.filtered(lambda c: c.state == 'active')
            )

    def action_view_sponsorships(self):
        """View all sponsorships for this partner"""
        self.ensure_one()
        
        action = self.env.ref('vertical_association_sweden.vf_sponsor_action').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_view_merchandise_orders(self):
        """View merchandise orders for this partner"""
        self.ensure_one()
        
        action = self.env.ref('vertical_association_sweden.vf_merchandise_order_action').read()[0]
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_create_sponsorship(self):
        """Create a new sponsorship for this partner"""
        self.ensure_one()
        
        return {
            'name': _('Create Sponsorship'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.sponsor',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.id,
                'default_is_sponsor': True,
            },
        }

    def action_create_merchandise_order(self):
        """Create a merchandise order for this partner"""
        self.ensure_one()
        
        return {
            'name': _('Create Merchandise Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.merchandise.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.id,
            },
        }
