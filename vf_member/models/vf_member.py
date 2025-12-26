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
        groups='vf_base.vf_admin'
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
    
    _sql_constraints = [
        ('membership_number_unique', 'unique(membership_number)', 
         'Membership number must be unique!'),
        ('partner_unique', 'unique(partner_id)', 
         'A person can only have one membership record!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('membership_number'):
                vals['membership_number'] = self._generate_membership_number()
        return super().create(vals_list)

    def _generate_membership_number(self):
        """Generate a unique membership number"""
        sequence = self.env['ir.sequence'].next_by_code('vf.member.sequence')
        if not sequence:
            # Create sequence if it doesn't exist
            self.env['ir.sequence'].create({
                'name': 'Member Sequence',
                'code': 'vf.member.sequence',
                'prefix': 'VF',
                'padding': 6,
            })
            sequence = self.env['ir.sequence'].next_by_code('vf.member.sequence')
        return sequence

    @api.depends('partner_id.birth_date')
    def _compute_is_minor(self):
        today = date.today()
        for member in self:
            if member.partner_id.birth_date:
                age = today.year - member.partner_id.birth_date.year - (
                    (today.month, today.day) < (member.partner_id.birth_date.month, 
                    member.partner_id.birth_date.day)
                )
                member.is_minor = age < 18
            else:
                member.is_minor = False

    @api.depends('partner_id.birth_date')
    def _compute_age(self):
        today = date.today()
        for member in self:
            if member.partner_id.birth_date:
                age = today.year - member.partner_id.birth_date.year - (
                    (today.month, today.day) < (member.partner_id.birth_date.month, 
                    member.partner_id.birth_date.day)
                )
                member.age = age
            else:
                member.age = 0

    def _search_age(self, operator, value):
        """Search members by age"""
        if operator not in ('=', '!=', '<', '<=', '>', '>=', 'in', 'not in'):
            raise UserError(_('Invalid operator for age search'))
        
        today = date.today()
        birth_dates = []
        
        if operator == '=':
            birth_year = today.year - value
            birth_dates.append((birth_year, today.month, today.day))
        elif operator == '<':
            for age in range(value + 1, 100):
                birth_year = today.year - age
                birth_dates.append((birth_year, today.month, today.day))
        elif operator == '>':
            for age in range(0, value):
                birth_year = today.year - age
                birth_dates.append((birth_year, today.month, today.day))
        # Add more operators as needed
        
        if birth_dates:
            domain = []
            for year, month, day in birth_dates:
                domain.append([
                    ('partner_id.birth_date', '<=', f'{year}-{month:02d}-{day:02d}'),
                    ('partner_id.birth_date', '>', f'{year-1}-{month:02d}-{day:02d}')
                ])
            return ['|'] * (len(domain) - 1) + [item for sublist in domain for item in sublist]
        return []

    @api.depends('guardian_ids.is_active')
    def _compute_has_active_guardians(self):
        for member in self:
            member.has_active_guardians = any(
                guardian.is_active for guardian in member.guardian_ids
            )

    @api.constrains('partner_id')
    def _check_partner_not_company(self):
        for member in self:
            if member.partner_id.is_company:
                raise ValidationError(_('A company cannot be a member. Only persons can be members.'))

    @api.constrains('is_minor', 'guardian_ids')
    def _check_minor_has_guardian(self):
        for member in self:
            if member.is_minor and not member.has_active_guardians:
                raise ValidationError(_('Minor members must have at least one active guardian.'))

    def action_archive(self):
        """Archive member instead of deleting"""
        for member in self:
            member.write({'active': False, 'status': 'archived'})
        return True

    def action_activate(self):
        """Activate archived member"""
        for member in self:
            member.write({'active': True, 'status': 'active'})
        return True

    def name_get(self):
        """Display membership number and partner name"""
        result = []
        for member in self:
            name = f'{member.membership_number} - {member.partner_id.name}'
            result.append((member.id, name))
        return result
