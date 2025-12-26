# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    # Portal member link
    vf_member_id = fields.Many2one(
        'vf.member',
        string='Association Member',
        help='Link this user to an association member'
    )
    is_portal_member = fields.Boolean(
        string='Is Portal Member',
        compute='_compute_is_portal_member',
        store=True
    )
    
    # Portal settings
    portal_member_settings_id = fields.Many2one(
        'vf.portal.member',
        string='Portal Settings'
    )
    
    @api.depends('vf_member_id')
    def _compute_is_portal_member(self):
        for user in self:
            user.is_portal_member = bool(user.vf_member_id)

    @api.model
    def create_portal_user(self, member, email, password=None):
        """Create portal user for member"""
        # Check if user already exists
        existing_user = self.search([('login', '=', email)])
        if existing_user:
            # Link to member if not already linked
            if not existing_user.vf_member_id:
                existing_user.vf_member_id = member.id
            return existing_user
        
        # Create new user
        groups = self.env.ref('base.group_portal')
        user_vals = {
            'name': member.partner_id.name,
            'login': email,
            'email': email,
            'partner_id': member.partner_id.id,
            'vf_member_id': member.id,
            'groups_id': [(6, 0, [groups.id])],
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, [self.env.company.id])],
        }
        
        if password:
            user_vals['password'] = password
        
        user = self.create(user_vals)
        
        # Create portal settings
        self.env['vf.portal.member'].create_or_update_portal_member(
            member.id, user.id
        )
        
        # Send welcome email
        if not password:
            # Send password setup email
            template = self.env.ref('vf_portal.email_template_portal_welcome')
            template.send_mail(user.id)
        
        return user

    def action_view_member_profile(self):
        """View member profile"""
        self.ensure_one()
        
        if not self.vf_member_id:
            raise ValidationError(_('No member linked to this user.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Member Profile',
            'res_model': 'vf.member',
            'res_id': self.vf_member_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_portal_dashboard(self):
        """Open portal dashboard"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/home',
            'target': 'self',
        }
