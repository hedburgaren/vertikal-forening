# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfPosition(models.Model):
    _name = 'vf.position'
    _description = 'Association Position'
    _order = 'section_id, group_id, name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Position Name',
        required=True,
        tracking=True
    )
    role_id = fields.Many2one(
        'vf.role',
        string='Role',
        required=True,
        tracking=True
    )
    
    # Assignment scope
    section_id = fields.Many2one(
        'vf.section',
        string='Section',
        tracking=True
    )
    group_id = fields.Many2one(
        'vf.group',
        string='Group',
        tracking=True
    )
    
    # Capacity
    max_holders = fields.Integer(
        string='Maximum Holders',
        default=1,
        tracking=True,
        help='Maximum number of people who can hold this position'
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
    current_holder_count = fields.Integer(
        string='Current Holders',
        compute='_compute_current_holder_count',
        store=True
    )
    
    # Relationships
    mandate_ids = fields.One2many(
        'vf.mandate',
        'position_id',
        string='Mandates'
    )

    @api.depends('name', 'role_id', 'section_id', 'group_id')
    def _compute_display_name(self):
        for position in self:
            parts = [position.name]
            
            if position.section_id:
                parts.append(f'({position.section_id.name})')
            elif position.group_id:
                parts.append(f'({position.group_id.name})')
            
            position.display_name = ' '.join(parts)

    @api.depends('mandate_ids.status')
    def _compute_current_holder_count(self):
        for position in self:
            position.current_holder_count = len(
                position.mandate_ids.filtered(lambda m: m.status == 'active')
            )

    @api.constrains('section_id', 'group_id')
    def _check_scope(self):
        for position in self:
            if position.section_id and position.group_id:
                if position.group_id.section_id != position.section_id:
                    raise ValidationError(_(
                        'Group must belong to the selected section.'
                    ))

    @api.constrains('max_holders')
    def _check_max_holders(self):
        for position in self:
            if position.max_holders < 1:
                raise ValidationError(_('Maximum holders must be at least 1.'))

    def action_view_mandates(self):
        """Open mandate view with this position's mandates"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_mandate_action').read()[0]
        action['domain'] = [('position_id', '=', self.id)]
        action['context'] = {'default_position_id': self.id}
        return action

    def action_assign_mandate(self):
        """Open wizard to assign a mandate"""
        self.ensure_one()
        return {
            'name': _('Assign Mandate'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.mandate.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_position_id': self.id},
        }

    def is_available(self):
        """Check if position has capacity for more holders"""
        return self.current_holder_count < self.max_holders
