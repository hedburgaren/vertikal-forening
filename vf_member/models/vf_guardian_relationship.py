# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class VfGuardianRelationship(models.Model):
    _name = 'vf.guardian.relationship'
    _description = 'Guardian Relationship for Minor Members'
    _order = 'member_id, sequence, guardian_id'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    member_id = fields.Many2one(
        'vf.member',
        string='Member (Minor)',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    guardian_id = fields.Many2one(
        'res.partner',
        string='Guardian',
        required=True,
        ondelete='cascade',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Relationship details
    relationship_type_id = fields.Many2one(
        'vf.relationship.type',
        string='Relationship Type',
        required=True,
        tracking=True,
        default=lambda self: self.env.ref('vf_member.relationship_type_primary').id
    )
    
    # Time management
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        tracking=True,
        help='Leave empty for ongoing guardianship'
    )
    
    # Status and flags
    is_active = fields.Boolean(
        string='Active',
        compute='_compute_is_active',
        store=True,
        tracking=True
    )
    is_primary = fields.Boolean(
        string='Primary Guardian',
        compute='_compute_is_primary',
        store=True,
        tracking=True
    )
    is_emergency = fields.Boolean(
        string='Emergency Contact',
        tracking=True
    )
    legal_custody = fields.Boolean(
        string='Legal Custody',
        tracking=True,
        help='Has legal custody of the minor'
    )
    
    # Contact information (can override partner's contact)
    emergency_phone = fields.Char(
        string='Emergency Phone',
        tracking=True
    )
    emergency_email = fields.Char(
        string='Emergency Email',
        tracking=True
    )
    
    # Administrative
    sequence = fields.Integer(
        string='Priority',
        default=10,
        help='Lower number = higher priority'
    )
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
        ('unique_guardian_member', 
         'UNIQUE(member_id, guardian_id, start_date, end_date)', 
         'A guardian can only have one relationship with a member for the same period!'),
    ]

    @api.depends('start_date', 'end_date')
    def _compute_is_active(self):
        today = date.today()
        for rel in self:
            if rel.end_date:
                rel.is_active = rel.start_date <= today <= rel.end_date
            else:
                rel.is_active = rel.start_date <= today

    @api.depends('relationship_type_id')
    def _compute_is_primary(self):
        for rel in self:
            rel.is_primary = rel.relationship_type_id.code == 'primary'

    @api.depends('member_id', 'guardian_id', 'relationship_type_id')
    def _compute_display_name(self):
        for rel in self:
            rel.display_name = f'{rel.guardian_id.name} - {rel.relationship_type_id.name} of {rel.member_id.partner_id.name}'

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rel in self:
            if rel.end_date and rel.start_date > rel.end_date:
                raise ValidationError(_('Start date must be before end date.'))

    @api.constrains('member_id')
    def _check_member_is_minor(self):
        for rel in self:
            if not rel.member_id.is_minor:
                raise ValidationError(_('Guardian relationships can only be created for minor members.'))

    @api.constrains('member_id', 'relationship_type_id')
    def _check_primary_guardian_limit(self):
        """Ensure only one primary guardian per member"""
        for rel in self:
            if rel.relationship_type_id.code == 'primary':
                primary_count = self.search([
                    ('member_id', '=', rel.member_id.id),
                    ('relationship_type_id.code', '=', 'primary'),
                    ('is_active', '=', True),
                    ('id', '!=', rel.id)
                ])
                if primary_count:
                    raise ValidationError(_('A member can only have one primary guardian at a time.'))

    def action_end_relationship(self, end_date=None):
        """End the guardian relationship"""
        if not end_date:
            end_date = date.today()
        self.write({'end_date': end_date})
        return True

    def action_reactivate(self):
        """Reactivate an ended relationship"""
        self.write({'end_date': False})
        return True

    @api.model
    def get_active_guardians(self, member_id):
        """Get all active guardians for a member"""
        return self.search([
            ('member_id', '=', member_id),
            ('is_active', '=', True)
        ])

    @api.model
    def get_primary_guardian(self, member_id):
        """Get the primary guardian for a member"""
        return self.search([
            ('member_id', '=', member_id),
            ('relationship_type_id.code', '=', 'primary'),
            ('is_active', '=', True)
        ], limit=1)

    @api.model
    def get_emergency_contacts(self, member_id):
        """Get all emergency contacts for a member"""
        return self.search([
            ('member_id', '=', member_id),
            ('is_active', '=', True),
            ('is_emergency', '=', True)
        ])
