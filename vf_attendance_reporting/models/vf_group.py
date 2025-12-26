# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class VfGroup(models.Model):
    _inherit = 'vf.group'

    # Group attendance statistics
    group_attendance_rate = fields.Float(
        compute='_compute_group_attendance',
        string='Group Attendance Rate (%)',
        digits=(5, 2)
    )
    total_member_attendances = fields.Integer(
        compute='_compute_group_attendance',
        string='Total Member Attendances'
    )
    active_members_this_month = fields.Integer(
        compute='_compute_monthly_activity',
        string='Active Members This Month'
    )
    
    # Top attendees
    top_attendees_ids = fields.Many2many(
        'vf.member',
        compute='_compute_top_attendees',
        string='Top Attendees'
    )

    def _compute_group_attendance(self):
        """Compute group attendance statistics"""
        for group in self:
            # Get all members in the group
            members = self.env['vf.member'].search([('group_ids', 'in', [group.id])])
            
            if not members:
                group.group_attendance_rate = 0
                group.total_member_attendances = 0
                continue
            
            # Get all attendances for group members
            attendances = self.env['vf.activity.attendance'].search([
                ('member_id', 'in', members.ids),
                ('state', '=', 'present'),
            ])
            
            # Get all registrations for group members
            registrations = self.env['vf.activity.registration'].search([
                ('member_id', 'in', members.ids),
                ('state', '=', 'confirmed'),
            ])
            
            group.total_member_attendances = len(attendances)
            
            if len(registrations) > 0:
                group.group_attendance_rate = (len(attendances) / len(registrations) * 100)
            else:
                group.group_attendance_rate = 0

    def _compute_monthly_activity(self):
        """Compute monthly activity statistics"""
        for group in self:
            today = fields.Date.today()
            month_start = today.replace(day=1)
            
            # Get members with activity this month
            active_members = self.env['vf.activity.attendance'].search([
                ('member_id.group_ids', 'in', [group.id]),
                ('state', '=', 'present'),
                ('schedule_id.start_date', '>=', month_start),
            ]).mapped('member_id')
            
            group.active_members_this_month = len(set(active_members))

    def _compute_top_attendees(self):
        """Compute top attendees in the group"""
        for group in self:
            # Get all members in the group
            members = self.env['vf.member'].search([('group_ids', 'in', [group.id])])
            
            # Sort by total activities attended
            sorted_members = sorted(members, key=lambda m: m.total_activities_attended, reverse=True)
            
            # Get top 5
            group.top_attendees_ids = [(6, 0, sorted_members[:5].ids)]

    def action_group_attendance_report(self):
        """Generate group attendance report"""
        self.ensure_one()
        
        # Create report
        report = self.env['vf.attendance.report'].create({
            'name': f'{self.name} - Attendance Report',
            'report_type': 'summary',
            'date_from': fields.Date.today() - relativedelta(months=3),
            'date_to': fields.Date.today(),
            'group_ids': [(6, 0, [self.id])],
        })
        
        # Calculate report
        report.action_calculate()
        
        # Return report view
        return {
            'name': _('Group Attendance Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.attendance.report',
            'res_id': report.id,
            'view_mode': 'form',
            'target': 'current',
        }
