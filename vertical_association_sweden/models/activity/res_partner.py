# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Activity relationships
    organized_activity_ids = fields.One2many(
        'vf.activity',
        'organizer_id',
        string='Organized Activities'
    )
    instructed_schedule_ids = fields.One2many(
        'vf.activity.schedule',
        'instructor_id',
        string='Instructed Schedules'
    )
    assistant_schedule_ids = fields.Many2many(
        'vf.activity.schedule',
        'vf_schedule_assistant_rel',
        'partner_id',
        'schedule_id',
        string='Assisted Schedules'
    )
    
    # Registration and attendance
    registration_ids = fields.One2many(
        'vf.activity.registration',
        'partner_id',
        string='Activity Registrations'
    )
    attendance_ids = fields.One2many(
        'vf.activity.attendance',
        'partner_id',
        string='Activity Attendance'
    )
    
    # Statistics
    activity_count = fields.Integer(
        compute='_compute_activity_count',
        string='Activities Count'
    )
    upcoming_activities = fields.Integer(
        compute='_compute_upcoming_activities',
        string='Upcoming Activities'
    )
    
    # Resource management
    managed_resource_ids = fields.One2many(
        'vf.resource',
        'manager_id',
        string='Managed Resources'
    )

    def _compute_activity_count(self):
        """Compute total activities participated in"""
        for partner in self:
            partner.activity_count = len(partner.registration_ids.filtered(
                lambda r: r.state == 'confirmed'
            ))

    def _compute_upcoming_activities(self):
        """Compute upcoming activities"""
        for partner in self:
            now = fields.Datetime.now()
            partner.upcoming_activities = len(
                partner.registration_ids.filtered(
                    lambda r: r.state == 'confirmed' and 
                    r.schedule_id.start_date > now
                )
            )

    def action_view_activities(self):
        """View all activities for this partner"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_activity_action').read()[0]
        action['domain'] = [
            '|', ('organizer_id', '=', self.id),
                 ('schedule_ids.registration_ids.partner_id', '=', self.id)
        ]
        return action

    def action_view_registrations(self):
        """View activity registrations"""
        self.ensure_one()
        return {
            'name': _('Activity Registrations'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.registration',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
        }

    def action_register_activity(self):
        """Register for an activity"""
        self.ensure_one()
        return {
            'name': _('Register for Activity'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.registration',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_id': self.id},
        }
