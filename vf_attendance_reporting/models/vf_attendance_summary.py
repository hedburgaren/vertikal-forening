# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfAttendanceSummary(models.Model):
    _name = 'vf.attendance.summary'
    _description = 'Attendance Summary'
    _order = 'date desc'
    _rec_name = 'display_name'

    # Core fields
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        ondelete='cascade'
    )
    date = fields.Date(
        string='Date',
        required=True
    )
    
    # Attendance counts
    activities_attended = fields.Integer(
        string='Activities Attended',
        default=0
    )
    activities_registered = fields.Integer(
        string='Activities Registered',
        default=0
    )
    
    # Attendance rate
    attendance_rate = fields.Float(
        compute='_compute_attendance_rate',
        string='Attendance Rate (%)',
        digits=(5, 2),
        store=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    # Details
    activity_ids = fields.Many2many(
        'vf.activity.schedule',
        'vf_summary_activity_rel',
        'summary_id',
        'schedule_id',
        string='Activities'
    )
    
    _sql_constraints = [
        ('unique_member_date', 'unique(member_id, date)', 
         'Only one summary per member per date is allowed!'),
    ]

    @api.depends('member_id', 'date')
    def _compute_display_name(self):
        for summary in self:
            if summary.member_id and summary.date:
                summary.display_name = f'{summary.member_id.name} - {summary.date}'
            else:
                summary.display_name = 'Attendance Summary'

    @api.depends('activities_attended', 'activities_registered')
    def _compute_attendance_rate(self):
        for summary in self:
            if summary.activities_registered > 0:
                summary.attendance_rate = (summary.activities_attended / summary.activities_registered * 100)
            else:
                summary.attendance_rate = 0

    @api.model
    def generate_summaries(self, date=None):
        """Generate attendance summaries for all members"""
        if not date:
            date = fields.Date.today()
        
        # Get all active members
        members = self.env['vf.member'].search([('state', '=', 'active')])
        
        for member in members:
            # Check if summary already exists
            existing = self.search([
                ('member_id', '=', member.id),
                ('date', '=', date)
            ])
            
            if existing:
                continue
            
            # Get activities on this date
            schedules = self.env['vf.activity.schedule'].search([
                ('start_date', '=', date)
            ])
            
            # Get registrations for this member
            registrations = self.env['vf.activity.registration'].search([
                ('member_id', '=', member.id),
                ('schedule_id', 'in', schedules.ids),
                ('state', '=', 'confirmed')
            ])
            
            # Get attendances for this member
            attendances = self.env['vf.activity.attendance'].search([
                ('member_id', '=', member.id),
                ('schedule_id', 'in', schedules.ids),
                ('state', '=', 'present')
            ])
            
            # Create summary
            self.create({
                'member_id': member.id,
                'date': date,
                'activities_registered': len(registrations),
                'activities_attended': len(attendances),
                'activity_ids': [(6, 0, attendances.mapped('schedule_id').ids)],
            })
        
        return True

    @api.model
    def get_monthly_summary(self, member_id, year, month):
        """Get monthly attendance summary for a member"""
        # Get all summaries for the month
        summaries = self.search([
            ('member_id', '=', member_id),
            ('date', '>=', f'{year}-{month:02d}-01'),
            ('date', '<=', f'{year}-{month:02d}-31'),
        ])
        
        total_attended = sum(s.activities_attended for s in summaries)
        total_registered = sum(s.activities_registered for s in summaries)
        attendance_rate = (total_attended / total_registered * 100) if total_registered > 0 else 0
        
        return {
            'year': year,
            'month': month,
            'total_attended': total_attended,
            'total_registered': total_registered,
            'attendance_rate': round(attendance_rate, 2),
            'days_active': len(summaries),
        }

    @api.model
    def get_yearly_summary(self, member_id, year):
        """Get yearly attendance summary for a member"""
        monthly_data = []
        
        for month in range(1, 13):
            summary = self.get_monthly_summary(member_id, year, month)
            monthly_data.append(summary)
        
        total_attended = sum(m['total_attended'] for m in monthly_data)
        total_registered = sum(m['total_registered'] for m in monthly_data)
        attendance_rate = (total_attended / total_registered * 100) if total_registered > 0 else 0
        
        return {
            'year': year,
            'monthly_data': monthly_data,
            'total_attended': total_attended,
            'total_registered': total_registered,
            'attendance_rate': round(attendance_rate, 2),
            'active_months': len([m for m in monthly_data if m['total_registered'] > 0]),
        }
