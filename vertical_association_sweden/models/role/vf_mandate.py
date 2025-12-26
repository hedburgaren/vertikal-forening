# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class VfMandate(models.Model):
    _name = 'vf.mandate'
    _description = 'Position Mandate'
    _order = 'position_id, start_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    person_id = fields.Many2one(
        'res.partner',
        string='Person',
        required=True,
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    position_id = fields.Many2one(
        'vf.position',
        string='Position',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Time management
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True
    )
    
    # Status and appointment
    status = fields.Selection([
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ], string='Status', default='pending', required=True, tracking=True)
    
    # Approval
    approved_by = fields.Many2one(
        'res.partner',
        string='Approved By',
        tracking=True,
        readonly=True
    )
    approval_date = fields.Date(
        string='Approval Date',
        readonly=True
    )
    
    # Administrative
    notes = fields.Text(
        string='Notes',
        tracking=True,
        groups='vertical_association_sweden.group_vf_admin'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    is_current = fields.Boolean(
        compute='_compute_is_current',
        store=True
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_person_position_active', 
         'UNIQUE(person_id, position_id, start_date, end_date)', 
         'A person can only hold the same position once for the same period!'),
    ]

    @api.depends('person_id', 'position_id')
    def _compute_display_name(self):
        for mandate in self:
            mandate.display_name = f'{mandate.person_id.name} - {mandate.position_id.name}'

    @api.depends('start_date', 'end_date', 'status')
    def _compute_is_current(self):
        today = date.today()
        for mandate in self:
            if mandate.status == 'active':
                mandate.is_current = mandate.start_date <= today <= mandate.end_date
            else:
                mandate.is_current = False

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for mandate in self:
            if mandate.start_date > mandate.end_date:
                raise ValidationError(_('Start date must be before end date.'))

    @api.constrains('person_id', 'position_id', 'start_date', 'end_date')
    def _check_overlap(self):
        for mandate in self:
            overlapping = self.search([
                ('person_id', '=', mandate.person_id.id),
                ('position_id', '=', mandate.position_id.id),
                ('status', 'in', ['active', 'pending']),
                ('id', '!=', mandate.id),
                ('start_date', '<=', mandate.end_date),
                ('end_date', '>=', mandate.start_date),
            ])
            if overlapping:
                raise ValidationError(_('Mandate dates overlap with existing mandate.'))

    @api.constrains('position_id')
    def _check_position_capacity(self):
        for mandate in self:
            if mandate.status in ['active', 'pending']:
                active_count = self.search_count([
                    ('position_id', '=', mandate.position_id.id),
                    ('status', '=', 'active'),
                    ('id', '!=', mandate.id),
                ])
                if active_count >= mandate.position_id.max_holders:
                    raise ValidationError(_('Position has reached maximum capacity.'))

    def action_approve(self):
        """Approve the mandate"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_('Only pending mandates can be approved.'))
        
        self.write({
            'status': 'active',
            'approved_by': self.env.user.partner_id,
            'approval_date': date.today(),
        })
        return True

    def action_revoke(self):
        """Revoke the mandate"""
        self.ensure_one()
        if self.status != 'active':
            raise UserError(_('Only active mandates can be revoked.'))
        
        self.write({'status': 'revoked'})
        return True

    def action_extend(self, new_end_date):
        """Extend the mandate end date"""
        self.ensure_one()
        if self.status != 'active':
            raise UserError(_('Only active mandates can be extended.'))
        
        if new_end_date <= self.end_date:
            raise UserError(_('New end date must be after current end date.'))
        
        self.write({'end_date': new_end_date})
        return True

    @api.model
    def get_current_mandates(self, person_id):
        """Get all current mandates for a person"""
        return self.search([
            ('person_id', '=', person_id),
            ('is_current', '=', True)
        ])

    @api.model
    def get_position_holders(self, position_id):
        """Get all current holders of a position"""
        return self.search([
            ('position_id', '=', position_id),
            ('is_current', '=', True)
        ])

    @api.model
    def get_expired_mandates(self, days=30):
        """Get mandates expiring within X days"""
        cutoff_date = date.today() + timedelta(days=days)
        return self.search([
            ('status', '=', 'active'),
            ('end_date', '<=', cutoff_date),
            ('end_date', '>=', date.today()),
        ])
