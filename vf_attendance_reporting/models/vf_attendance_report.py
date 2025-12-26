# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from datetime import datetime, timedelta
import calendar


class VfAttendanceReport(models.Model):
    _name = 'vf.attendance.report'
    _description = 'Attendance Report'
    _order = 'date_from desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Report configuration
    name = fields.Char(
        string='Report Name',
        required=True,
        tracking=True
    )
    report_type = fields.Selection([
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('absence', 'Absence Report'),
        ('trend', 'Trend Analysis'),
    ], string='Report Type', required=True, default='summary', tracking=True)
    
    # Date range
    date_from = fields.Date(
        string='From Date',
        required=True,
        tracking=True
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        tracking=True
    )
    
    # Filters
    member_ids = fields.Many2many(
        'vf.member',
        'vf_report_member_rel',
        'report_id',
        'member_id',
        string='Members'
    )
    group_ids = fields.Many2many(
        'vf.group',
        'vf_report_group_rel',
        'report_id',
        'group_id',
        string='Groups'
    )
    section_ids = fields.Many2many(
        'vf.section',
        'vf_report_section_rel',
        'report_id',
        'section_id',
        string='Sections'
    )
    activity_type_ids = fields.Many2many(
        'vf.activity.type',
        'vf_report_activity_type_rel',
        'report_id',
        'activity_type_id',
        string='Activity Types'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculating', 'Calculating'),
        ('ready', 'Ready'),
        ('error', 'Error'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    # Report data (stored as JSON)
    report_data = fields.Text(
        string='Report Data',
        help='JSON data for the report'
    )
    
    # Generated files
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Generated File',
        readonly=True
    )
    
    # Statistics
    total_activities = fields.Integer(
        compute='_compute_statistics',
        string='Total Activities'
    )
    total_attendances = fields.Integer(
        compute='_compute_statistics',
        string='Total Attendances'
    )
    attendance_rate = fields.Float(
        compute='_compute_statistics',
        string='Attendance Rate (%)',
        digits=(5, 2)
    )
    unique_members = fields.Integer(
        compute='_compute_statistics',
        string='Unique Members'
    )

    @api.depends('name', 'date_from', 'date_to')
    def _compute_display_name(self):
        for report in self:
            if report.date_from and report.date_to:
                date_str = f'{report.date_from} to {report.date_to}'
                report.display_name = f'{report.name} ({date_str})'
            else:
                report.display_name = report.name

    @api.depends('report_data')
    def _compute_statistics(self):
        """Compute statistics from report data"""
        for report in self:
            if report.report_data:
                try:
                    import json
                    data = json.loads(report.report_data)
                    report.total_activities = data.get('total_activities', 0)
                    report.total_attendances = data.get('total_attendances', 0)
                    report.attendance_rate = data.get('attendance_rate', 0)
                    report.unique_members = data.get('unique_members', 0)
                except:
                    report.total_activities = 0
                    report.total_attendances = 0
                    report.attendance_rate = 0
                    report.unique_members = 0
            else:
                report.total_activities = 0
                report.total_attendances = 0
                report.attendance_rate = 0
                report.unique_members = 0

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for report in self:
            if report.date_from >= report.date_to:
                raise ValidationError(_('To date must be after from date.'))

    def action_calculate(self):
        """Calculate the report"""
        self.write({'state': 'calculating'})
        
        for report in self:
            try:
                if report.report_type == 'summary':
                    data = report._calculate_summary_report()
                elif report.report_type == 'detailed':
                    data = report._calculate_detailed_report()
                elif report.report_type == 'absence':
                    data = report._calculate_absence_report()
                elif report.report_type == 'trend':
                    data = report._calculate_trend_report()
                else:
                    raise ValueError(_('Unknown report type'))
                
                report.write({
                    'report_data': data,
                    'state': 'ready',
                })
                
            except Exception as e:
                report.write({
                    'state': 'error',
                })
                report.message_post(
                    body=_('Error calculating report: %s') % str(e),
                    message_type='notification'
                )
        
        return True

    def _calculate_summary_report(self):
        """Calculate summary report data"""
        import json
        
        # Get attendance records in date range
        domain = [
            ('schedule_id.start_date', '>=', self.date_from),
            ('schedule_id.start_date', '<=', self.date_to),
            ('state', '=', 'present'),
        ]
        
        # Apply filters
        if self.member_ids:
            domain.append(('member_id', 'in', self.member_ids.ids))
        if self.group_ids:
            domain.append(('member_id.group_ids', 'in', self.group_ids.ids))
        if self.section_ids:
            domain.append(('member_id.section_ids', 'in', self.section_ids.ids))
        
        attendances = self.env['vf.activity.attendance'].search(domain)
        
        # Calculate statistics
        total_activities = self.env['vf.activity.schedule'].search_count([
            ('start_date', '>=', self.date_from),
            ('start_date', '<=', self.date_to),
        ])
        
        total_registrations = self.env['vf.activity.registration'].search_count([
            ('schedule_id.start_date', '>=', self.date_from),
            ('schedule_id.start_date', '<=', self.date_to),
            ('state', '=', 'confirmed'),
        ])
        
        attendance_rate = (len(attendances) / total_registrations * 100) if total_registrations > 0 else 0
        unique_members = len(attendances.mapped('member_id'))
        
        # Group by member
        member_stats = {}
        for attendance in attendances:
            member_id = attendance.member_id.id
            if member_id not in member_stats:
                member_stats[member_id] = {
                    'name': attendance.member_id.name,
                    'attended': 0,
                }
            member_stats[member_id]['attended'] += 1
        
        # Sort by attendance count
        sorted_members = sorted(member_stats.values(), key=lambda x: x['attended'], reverse=True)[:10]
        
        data = {
            'total_activities': total_activities,
            'total_attendances': len(attendances),
            'attendance_rate': round(attendance_rate, 2),
            'unique_members': unique_members,
            'top_attendees': sorted_members,
        }
        
        return json.dumps(data)

    def _calculate_detailed_report(self):
        """Calculate detailed report data"""
        import json
        
        # Get all activities in date range
        domain = [
            ('start_date', '>=', self.date_from),
            ('start_date', '<=', self.date_to),
        ]
        
        if self.activity_type_ids:
            domain.append(('activity_id.activity_type_id', 'in', self.activity_type_ids.ids))
        
        schedules = self.env['vf.activity.schedule'].search(domain)
        
        activities_data = []
        for schedule in schedules:
            attendance_count = self.env['vf.activity.attendance'].search_count([
                ('schedule_id', '=', schedule.id),
                ('state', '=', 'present'),
            ])
            
            registration_count = self.env['vf.activity.registration'].search_count([
                ('schedule_id', '=', schedule.id),
                ('state', '=', 'confirmed'),
            ])
            
            activities_data.append({
                'activity': schedule.name,
                'date': schedule.start_date.strftime('%Y-%m-%d'),
                'type': schedule.activity_id.activity_type_id.name,
                'registered': registration_count,
                'attended': attendance_count,
                'rate': round((attendance_count / registration_count * 100) if registration_count > 0 else 0, 2),
            })
        
        data = {
            'activities': activities_data,
            'total_activities': len(schedules),
        }
        
        return json.dumps(data)

    def _calculate_absence_report(self):
        """Calculate absence report data"""
        import json
        
        # Get registrations without attendance
        domain = [
            ('schedule_id.start_date', '>=', self.date_from),
            ('schedule_id.start_date', '<=', self.date_to),
            ('state', '=', 'confirmed'),
        ]
        
        # Apply filters
        if self.member_ids:
            domain.append(('member_id', 'in', self.member_ids.ids))
        if self.group_ids:
            domain.append(('member_id.group_ids', 'in', self.group_ids.ids))
        
        registrations = self.env['vf.activity.registration'].search(domain)
        
        # Find absent members
        absent_data = {}
        for registration in registrations:
            attendance = self.env['vf.activity.attendance'].search([
                ('schedule_id', '=', registration.schedule_id.id),
                ('member_id', '=', registration.member_id.id),
            ])
            
            if not attendance:
                member_id = registration.member_id.id
                if member_id not in absent_data:
                    absent_data[member_id] = {
                        'name': registration.member_id.name,
                        'absences': 0,
                        'activities': [],
                    }
                
                absent_data[member_id]['absences'] += 1
                absent_data[member_id]['activities'].append({
                    'activity': registration.schedule_id.name,
                    'date': registration.schedule_id.start_date.strftime('%Y-%m-%d'),
                })
        
        # Sort by absence count
        sorted_absences = sorted(absent_data.values(), key=lambda x: x['absences'], reverse=True)
        
        data = {
            'absent_members': sorted_absences,
            'total_absences': sum(m['absences'] for m in sorted_absences),
        }
        
        return json.dumps(data)

    def _calculate_trend_report(self):
        """Calculate trend analysis data"""
        import json
        
        # Group by month
        monthly_data = {}
        current = self.date_from.replace(day=1)
        
        while current <= self.date_to:
            month_end = current.replace(day=calendar.monthrange(current.year, current.month)[1])
            month_key = current.strftime('%Y-%m')
            
            # Get attendance for this month
            domain = [
                ('schedule_id.start_date', '>=', current),
                ('schedule_id.start_date', '<=', month_end),
                ('state', '=', 'present'),
            ]
            
            attendances = self.env['vf.activity.attendance'].search(domain)
            registrations = self.env['vf.activity.registration'].search([
                ('schedule_id.start_date', '>=', current),
                ('schedule_id.start_date', '<=', month_end),
                ('state', '=', 'confirmed'),
            ])
            
            monthly_data[month_key] = {
                'month': current.strftime('%B %Y'),
                'activities': len(registrations.mapped('schedule_id')),
                'registrations': len(registrations),
                'attendances': len(attendances),
                'rate': round((len(attendances) / len(registrations) * 100) if registrations else 0, 2),
            }
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1, day=1)
            else:
                current = current.replace(month=current.month + 1, day=1)
        
        data = {
            'monthly_trend': list(monthly_data.values()),
        }
        
        return json.dumps(data)

    def action_export_excel(self):
        """Export report to Excel"""
        self.ensure_one()
        
        if self.state != 'ready':
            return False
        
        # Generate Excel file
        import json
        import io
        import xlsxwriter
        
        data = json.loads(self.report_data)
        
        # Create workbook
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        if self.report_type == 'summary':
            worksheet = workbook.add_worksheet('Summary')
            
            # Headers
            worksheet.write(0, 0, 'Metric')
            worksheet.write(0, 1, 'Value')
            
            # Data
            worksheet.write(1, 0, 'Total Activities')
            worksheet.write(1, 1, data.get('total_activities', 0))
            worksheet.write(2, 0, 'Total Attendances')
            worksheet.write(2, 1, data.get('total_attendances', 0))
            worksheet.write(3, 0, 'Attendance Rate (%)')
            worksheet.write(3, 1, data.get('attendance_rate', 0))
            worksheet.write(4, 0, 'Unique Members')
            worksheet.write(4, 1, data.get('unique_members', 0))
            
            # Top attendees
            if data.get('top_attendees'):
                worksheet.write(6, 0, 'Top Attendees')
                worksheet.write(7, 0, 'Member')
                worksheet.write(7, 1, 'Sessions Attended')
                
                row = 8
                for attendee in data['top_attendees']:
                    worksheet.write(row, 0, attendee['name'])
                    worksheet.write(row, 1, attendee['attended'])
                    row += 1
        
        workbook.close()
        output.seek(0)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}.xlsx',
            'type': 'binary',
            'datas': output.read(),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        self.attachment_id = attachment.id
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
