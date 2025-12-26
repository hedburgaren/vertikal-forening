# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class VfMember(models.Model):
    _name = 'vf.member'
    _description = 'Association Member'
    _order = 'membership_number'
    _rec_name = 'membership_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    partner_id = fields.Many2one(
        'res.partner',
        string='Person',
        required=True,
        tracking=True,
        ondelete='cascade',
        domain=[('is_company', '=', False)]
    )
    membership_number = fields.Char(
        string='Membership Number',
        readonly=True,
        copy=False,
        tracking=True
    )
    membership_date = fields.Date(
        string='Membership Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    # Status and classification
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('archived', 'Archived'),
    ], string='Status', default='active', required=True, tracking=True)
    is_minor = fields.Boolean(
        string='Is Minor',
        compute='_compute_is_minor',
        store=True,
        help='Automatically computed from birth date'
    )
    
    # Age calculation
    age = fields.Integer(
        string='Age',
        compute='_compute_age',
        search='_search_age'
    )
    birth_date = fields.Date(
        related='partner_id.birth_date',
        string='Birth Date',
        readonly=True,
        store=True
    )
    
    # Relationships
    guardian_ids = fields.One2many(
        'vf.guardian.relationship',
        'member_id',
        string='Guardians'
    )
    family_relationship_ids = fields.One2many(
        'vf.family.relationship',
        'member_id',
        string='Family Relationships'
    )
    household_id = fields.Many2one(
        'vf.household',
        string='Household',
        tracking=True
    )
    
    # Group memberships
    group_membership_ids = fields.One2many(
        'vf.group.membership',
        'member_id',
        string='Group Memberships'
    )
    
    # Administrative fields
    notes = fields.Text(
        string='Administrative Notes',
        tracking=True,
        groups='vertical_association_sweden.group_vf_admin'
    )
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    # Computed fields
    has_active_guardians = fields.Boolean(
        compute='_compute_has_active_guardians',
        store=True
    )
    
    @api.depends('partner_id.birth_date')
    def _compute_is_minor(self):
        today = date.today()
        for member in self:
            if member.partner_id.birth_date:
                age = today.year - member.partner_id.birth_date.year - (
                    (today.month, today.day) < (member.partner_id.birth_date.month, member.partner_id.birth_date.day)
                )
                member.is_minor = age < 18
            else:
                member.is_minor = False
    
    @api.depends('partner_id.birth_date')
    def _compute_age(self):
        today = date.today()
        for member in self:
            if member.partner_id.birth_date:
                member.age = today.year - member.partner_id.birth_date.year - (
                    (today.month, today.day) < (member.partner_id.birth_date.month, member.partner_id.birth_date.day)
                )
            else:
                member.age = 0
    
    def _search_age(self, operator, value):
        if operator not in ('=', '!=', '<', '<=', '>', '>=', 'in', 'not in'):
            raise ValueError(_('Invalid operator'))
        
        today = date.today()
        min_birth_date = None
        max_birth_date = None
        
        if operator == '=':
            min_birth_date = today.replace(year=today.year - value - 1)
            max_birth_date = today.replace(year=today.year - value)
        elif operator == '<':
            max_birth_date = today.replace(year=today.year - value)
        elif operator == '<=':
            max_birth_date = today.replace(year=today.year - value - 1)
        elif operator == '>':
            min_birth_date = today.replace(year=today.year - value - 1)
        elif operator == '>=':
            min_birth_date = today.replace(year=today.year - value)
        
        domain = []
        if min_birth_date:
            domain.append(('partner_id.birth_date', '>=', min_birth_date))
        if max_birth_date:
            domain.append(('partner_id.birth_date', '<', max_birth_date))
        
        if operator in ('!=', 'not in'):
            return ['&'] + domain if domain else []
        return domain
    
    @api.depends('guardian_ids.is_active')
    def _compute_has_active_guardians(self):
        for member in self:
            member.has_active_guardians = any(
                guardian.is_active for guardian in member.guardian_ids
            )
    
    @api.model
    def create(self, vals):
        if 'membership_number' not in vals:
            vals['membership_number'] = self._generate_membership_number()
        return super().create(vals)
    
    def _generate_membership_number(self):
        sequence = self.env['ir.sequence'].next_by_code('vf.member') or '/'
        return sequence
    
    def action_activate(self):
        self.write({'active': True, 'status': 'active'})
    
    def action_archive(self):
        self.write({'active': False, 'status': 'archived'})
    
    def action_view_guardians(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Guardians',
            'res_model': 'vf.guardian.relationship',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id},
        }
    
    def action_view_groups(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Group Memberships',
            'res_model': 'vf.group.membership',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id},
        }
    
    @api.constrains('partner_id')
    def _check_partner_unique(self):
        for member in self:
            existing = self.search([
                ('partner_id', '=', member.partner_id.id),
                ('id', '!=', member.id)
            ])
            if existing:
                raise ValidationError(_('A person can only be a member once.'))
    
    @api.constrains('partner_id')
    def _check_guardians_for_minor(self):
        for member in self:
            if member.is_minor and not member.has_active_guardians:
                raise ValidationError(_('Minor members must have at least one active guardian.'))
