# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request
from odoo.exceptions import AccessError, ValidationError
import json


class VfMemberController(http.Controller):
    
    @http.route('/member/profile', type='json', auth='user', website=True)
    def member_profile(self):
        """Get current user's member profile"""
        if not request.env.user.has_group('vf_base.group_vf_user'):
            raise AccessError('Access denied')
        
        partner = request.env.user.partner_id
        if not partner.member_id:
            return {'error': 'User is not a member'}
        
        member = partner.member_id
        return {
            'member': {
                'id': member.id,
                'membership_number': member.membership_number,
                'membership_date': member.membership_date,
                'status': member.status,
                'age': member.age,
                'is_minor': member.is_minor,
            },
            'partner': {
                'id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
                'birth_date': partner.birth_date,
            }
        }
    
    @http.route('/member/guardians/<int:member_id>', type='json', auth='user', website=True)
    def member_guardians(self, member_id):
        """Get guardians for a member (if user has access)"""
        if not request.env.user.has_group('vf_base.group_vf_user'):
            raise AccessError('Access denied')
        
        member = request.env['vf.member'].browse(member_id)
        
        # Check access: own data or guardian
        if member.partner_id.id != request.env.user.partner_id.id:
            is_guardian = request.env['vf.guardian.relationship'].search([
                ('member_id', '=', member_id),
                ('guardian_id', '=', request.env.user.partner_id.id),
                ('is_active', '=', True)
            ])
            if not is_guardian and not request.env.user.has_group('vf_base.group_vf_admin'):
                raise AccessError('Access denied')
        
        guardians = []
        for rel in member.guardian_ids.filtered('is_active'):
            guardians.append({
                'id': rel.id,
                'guardian': {
                    'id': rel.guardian_id.id,
                    'name': rel.guardian_id.name,
                    'phone': rel.emergency_phone or rel.guardian_id.phone,
                    'email': rel.emergency_email or rel.guardian_id.email,
                },
                'relationship_type': rel.relationship_type_id.name,
                'is_primary': rel.is_primary,
                'is_emergency': rel.is_emergency,
                'legal_custody': rel.legal_custody,
            })
        
        return {'guardians': guardians}
    
    @http.route('/member/household/<int:member_id>', type='json', auth='user', website=True)
    def member_household(self, member_id):
        """Get household information for a member"""
        if not request.env.user.has_group('vf_base.group_vf_user'):
            raise AccessError('Access denied')
        
        member = request.env['vf.member'].browse(member_id)
        
        # Check access
        if member.partner_id.id != request.env.user.partner_id.id:
            is_guardian = request.env['vf.guardian.relationship'].search([
                ('member_id', '=', member_id),
                ('guardian_id', '=', request.env.user.partner_id.id),
                ('is_active', '=', True)
            ])
            if not is_guardian and not request.env.user.has_group('vf_base.group_vf_admin'):
                raise AccessError('Access denied')
        
        if not member.household_id:
            return {'household': None}
        
        household = member.household_id
        household_members = []
        for m in household.member_ids:
            # Only show members user has access to
            if (m.partner_id.id == request.env.user.partner_id.id or
                request.env.user.has_group('vf_base.group_vf_admin') or
                request.env['vf.guardian.relationship'].search([
                    ('member_id', '=', m.id),
                    ('guardian_id', '=', request.env.user.partner_id.id),
                    ('is_active', '=', True)
                ])):
                household_members.append({
                    'id': m.id,
                    'name': m.partner_id.name,
                    'membership_number': m.membership_number,
                    'age': m.age,
                    'is_minor': m.is_minor,
                })
        
        return {
            'household': {
                'id': household.id,
                'name': household.name,
                'address': {
                    'street': household.street,
                    'street2': household.street2,
                    'zip': household.zip,
                    'city': household.city,
                    'state': household.state_id.name,
                    'country': household.country_id.name,
                },
                'phone': household.phone,
                'email': household.email,
            },
            'members': household_members
        }
