# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfFamilyRelationship(models.Model):
    _name = 'vf.family.relationship'
    _description = 'Family Relationship Between Members'
    _order = 'member_id, related_member_id'
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
    related_member_id = fields.Many2one(
        'vf.member',
        string='Related Member',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Relationship details
    relationship_type_id = fields.Many2one(
        'vf.relationship.type',
        string='Relationship Type',
        required=True,
        tracking=True,
        domain="[('code', 'in', ['sibling', 'parent_adult', 'spouse', 'other'])]"
    )
    
    # Household connection
    household_id = fields.Many2one(
        'vf.household',
        string='Household',
        tracking=True
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
        ('unique_relationship', 
         'UNIQUE(member_id, related_member_id, relationship_type_id)', 
         'This relationship already exists!'),
        ('not_self', 
         'CHECK(member_id != related_member_id)', 
         'A member cannot be related to themselves!'),
    ]

    @api.depends('member_id', 'related_member_id', 'relationship_type_id')
    def _compute_display_name(self):
        for rel in self:
            rel.display_name = f'{rel.member_id.partner_id.name} is {rel.relationship_type_id.name} of {rel.related_member_id.partner_id.name}'

    @api.constrains('member_id', 'related_member_id')
    def _check_reciprocal_relationship(self):
        """Ensure reciprocal relationships are consistent"""
        for rel in self:
            # Check if reverse relationship exists
            reverse = self.search([
                ('member_id', '=', rel.related_member_id.id),
                ('related_member_id', '=', rel.member_id.id),
                ('id', '!=', rel.id)
            ])
            
            # For sibling relationships, ensure both directions exist
            if rel.relationship_type_id.code == 'sibling' and not reverse:
                # Create reverse relationship automatically
                self.create({
                    'member_id': rel.related_member_id.id,
                    'related_member_id': rel.member_id.id,
                    'relationship_type_id': rel.relationship_type_id.id,
                    'household_id': rel.household_id,
                })

    def action_create_reverse(self):
        """Manually create the reverse relationship"""
        for rel in self:
            if not self.search([
                ('member_id', '=', rel.related_member_id.id),
                ('related_member_id', '=', rel.member_id.id),
                ('relationship_type_id', '=', rel.relationship_type_id.id)
            ]):
                self.create({
                    'member_id': rel.related_member_id.id,
                    'related_member_id': rel.member_id.id,
                    'relationship_type_id': rel.relationship_type_id.id,
                    'household_id': rel.household_id,
                    'notes': rel.notes,
                })
        return True
