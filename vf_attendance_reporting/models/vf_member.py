# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta


class VfMember(models.Model):
    _inherit = 'vf.member'

    # Attendance relationships
    attendance_ids = fields.One2many(
        'vf.activity.attendance',
        'member_id',
        string='Attendance Records'
    )
    summary_ids = fields.One2many(
        'vf.attendance.summary',
        'member_id',
        string='Attendance Summaries'
    )
    
    # Attendance statistics
    total_activities_attended = fields.Integer(
        compute='_compute_attendance_statistics',
        string='Total Activities Attended'
    )
    total_activities_registered = fields.Integer(
        compute='_compute_attendance_statistics',
        string='Total Activities Registered'
    )
    overall_attendance_rate = fields.Float(
        compute='_compute_attendance_statistics',
        string='Overall Attendance Rate (%)',
        digits=(5, 2)
    )
    
    # Recent attendance
    last_attendance_date = fields.Date(
        compute='_compute_last_attendance',
        string='Last Attendance Date'
    )
    activities_this_month = fields.Integer(
        compute='_compute_monthly_attendance',
        string='Activities This Month'
    )
    activities_last_month = fields.Integer(
        compute='_compute_monthly_attendance',
        string='Activities Last Month'
    )
    
    # Attendance streak
    current_streak = fields.Integer(
        compute='_compute_attendance_streak',
        string='Current Streak (days)'
    )
    longest_streak = fields.Integer(
        compute='_compute_attendance_streak',
        string='Longest Streak (days)'
    )

    def _compute_attendance_statistics(self):
        """Compute overall attendance statistics"""
        for member in self:
            # Get all attendance records
            attendances = self.env['vf.activity.attendance'].search([
                ('member_id', '=', member.id),
                ('state', '=', 'present'),
            ])
            
            # Get all registration records
            registrations = self.env['vf.activity.registration'].search([
                ('member_id', '=', member.id),
                ('state', '=', 'confirmed'),
            ])
            
            member.total_activities_attended = len(attendances)
            member.total_activities_registered = len(registrations)
            
            if member.total_activities_registered > 0:
                member.overall_attendance_rate = (
                    member.total_activities_attended / member.total_activities_registered * 100
                )
            else:
                member.overall_attendance_rate = 0

    def _compute_last_attendance(self):
        """Compute last attendance date"""
        for member in self:
            last_attendance = self.env['vf.activity.attendance'].search([
                ('member_id', '=', member.id),
                ('state', '=', 'present'),
            ], order='schedule_id.start_date desc', limit=1)
            
            if last_attendance:
                member.last_attendance_date = last_attendance.schedule_id.start_date.date()
            else:
                member.last_attendance_date = False

    def _compute_monthly_attendance(self):
        """Compute monthly attendance counts"""
        for member in self:
            today = fields.Date.today()
            this_month_start = today.replace(day=1)
            last_month_start = (this_month_start - relativedelta(months=1))
            
            # This month
            this_month_attendances = self.env['vf.activity.attendance'].search_count([
                ('member_id', '=', member.id),
                ('state', '=', 'present'),
                ('schedule_id.start_date', '>=', this_month_start),
            ])
            
            # Last month
            last_month_attendances = self.env['vf.activity.attendance'].search_count([
                ('member_id', '=', member.id),
                ('state', '=', 'present'),
                ('schedule_id.start_date', '>=', last_month_start),
                ('schedule_id.start_date', '<', this_month_start),
            ])
            
            member.activities_this_month = this_month_attendances
            member.activities_last_month = last_month_attendances

    def _compute_attendance_streak(self):
        """Compute attendance streaks"""
        for member in self:
            # Get all attendance dates
            attendances = self.env['vf.activity.attendance'].search([
                ('member_id', '=', member.id),
                ('state', '=', 'present'),
            ], order='schedule_id.start_date desc')
            
            if not attendances:
                member.current_streak = 0
                member.longest_streak = 0
                continue
            
            # Calculate current streak
            current_streak = 0
            current_date = fields.Date.today()
            
            for attendance in attendances:
                att_date = attendance.schedule_id.start_date.date()
                
                if att_date == current_date or att_date == current_date - relativedelta(days=1):
                    current_streak += 1
                    current_date = att_date
                elif att_date < current_date - relativedelta(days=1):
                    break
            
            member.current_streak = current_streak
            
            # Calculate longest streak
            longest_streak = 0
            temp_streak = 1
            dates = [a.schedule_id.start_date.date() for a in attendances]
            
            for i in range(1, len(dates)):
                if dates[i-1] - dates[i] == relativedelta(days=1):
                    temp_streak += 1
                else:
                    longest_streak = max(longest_streak, temp_streak)
                    temp_streak = 1
            
            member.longest_streak = max(longest_streak, temp_streak)

    def action_view_attendance(self):
        """View member's attendance records"""
        self.ensure_one()
        return {
            'name': _('Attendance Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.attendance',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id},
        }

    def action_view_attendance_summary(self):
        """View member's attendance summaries"""
        self.ensure_one()
        return {
            'name': _('Attendance Summary'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.attendance.summary',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id},
        }

    def action_generate_monthly_report(self):
        """Generate monthly attendance report"""
        self.ensure_one()
        today = fields.Date.today()
        
        # Create report
        report = self.env['vf.attendance.report'].create({
            'name': f'{self.name} - Monthly Report',
            'report_type': 'summary',
            'date_from': today.replace(day=1),
            'date_to': today.replace(day=1) + relativedelta(months=1, days=-1),
            'member_ids': [(6, 0, [self.id])],
        })
        
        # Calculate report
        report.action_calculate()
        
        # Return report view
        return {
            'name': _('Monthly Attendance Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.attendance.report',
            'res_id': report.id,
            'view_mode': 'form',
            'target': 'current',
        }
