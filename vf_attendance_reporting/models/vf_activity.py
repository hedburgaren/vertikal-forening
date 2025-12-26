# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfActivity(models.Model):
    _inherit = 'vf.activity'

    # Activity attendance statistics
    activity_attendance_rate = fields.Float(
        compute='_compute_activity_attendance',
        string='Attendance Rate (%)',
        digits=(5, 2)
    )
    total_registrations = fields.Integer(
        compute='_compute_activity_attendance',
        string='Total Registrations'
    )
    total_attendances = fields.Integer(
        compute='_compute_activity_attendance',
        string='Total Attendances'
    )


class VfActivitySchedule(models.Model):
    _inherit = 'vf.activity.schedule'

    # Schedule attendance statistics
    schedule_attendance_rate = fields.Float(
        compute='_compute_schedule_attendance',
        string='Attendance Rate (%)',
        digits=(5, 2)
    )
    registration_count = fields.Integer(
        compute='_compute_schedule_attendance',
        string='Registration Count'
    )
    attendance_count = fields.Integer(
        compute='_compute_schedule_attendance',
        string='Attendance Count'
    )
    
    # Attendance details
    attended_member_ids = fields.Many2many(
        'vf.member',
        compute='_compute_attended_members',
        string='Attended Members'
    )
    absent_member_ids = fields.Many2many(
        'vf.member',
        compute='_compute_absent_members',
        string='Absent Members'
    )

    def _compute_schedule_attendance(self):
        """Compute schedule attendance statistics"""
        for schedule in self:
            # Get confirmed registrations
            registrations = self.env['vf.activity.registration'].search([
                ('schedule_id', '=', schedule.id),
                ('state', '=', 'confirmed'),
            ])
            
            # Get present attendances
            attendances = self.env['vf.activity.attendance'].search([
                ('schedule_id', '=', schedule.id),
                ('state', '=', 'present'),
            ])
            
            schedule.registration_count = len(registrations)
            schedule.attendance_count = len(attendances)
            
            if schedule.registration_count > 0:
                schedule.schedule_attendance_rate = (
                    schedule.attendance_count / schedule.registration_count * 100
                )
            else:
                schedule.schedule_attendance_rate = 0

    def _compute_attended_members(self):
        """Compute attended members"""
        for schedule in self:
            attendances = self.env['vf.activity.attendance'].search([
                ('schedule_id', '=', schedule.id),
                ('state', '=', 'present'),
            ])
            schedule.attended_member_ids = [(6, 0, attendances.mapped('member_id').ids)]

    def _compute_absent_members(self):
        """Compute absent members (registered but didn't attend)"""
        for schedule in self:
            # Get registered members
            registrations = self.env['vf.activity.registration'].search([
                ('schedule_id', '=', schedule.id),
                ('state', '=', 'confirmed'),
            ])
            registered_members = registrations.mapped('member_id')
            
            # Get attended members
            attendances = self.env['vf.activity.attendance'].search([
                ('schedule_id', '=', schedule.id),
                ('state', '=', 'present'),
            ])
            attended_members = attendances.mapped('member_id')
            
            # Find absent members
            absent_members = registered_members - attended_members
            schedule.absent_member_ids = [(6, 0, absent_members.ids)]

    def action_take_attendance(self):
        """Take attendance for this schedule"""
        self.ensure_one()
        
        # Create attendance records for all registered members
        registrations = self.env['vf.activity.registration'].search([
            ('schedule_id', '=', self.id),
            ('state', '=', 'confirmed'),
        ])
        
        action = {
            'name': _('Take Attendance'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_schedule_id': self.id,
                'default_registration_ids': registrations.ids,
            },
        }
        
        return action

    def action_view_attendance_report(self):
        """View attendance report for this activity"""
        self.ensure_one()
        
        # Create report for this activity
        report = self.env['vf.attendance.report'].create({
            'name': f'{self.name} - Attendance Report',
            'report_type': 'detailed',
            'date_from': self.start_date.date(),
            'date_to': self.end_date.date() if self.end_date else self.start_date.date(),
        })
        
        # Calculate report
        report.action_calculate()
        
        # Return report view
        return {
            'name': _('Activity Attendance Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.attendance.report',
            'res_id': report.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_export_attendance_list(self):
        """Export attendance list for this schedule"""
        self.ensure_one()
        
        # Generate attendance list
        registrations = self.env['vf.activity.registration'].search([
            ('schedule_id', '=', self.id),
            ('state', '=', 'confirmed'),
        ])
        
        attendances = self.env['vf.activity.attendance'].search([
            ('schedule_id', '=', self.id),
        ])
        
        # Create attendance list data
        data = []
        for registration in registrations:
            attendance = attendances.filtered(lambda a: a.member_id == registration.member_id)
            
            data.append({
                'member': registration.member_id.name,
                'registered': registration.registration_date.strftime('%Y-%m-%d'),
                'attended': attendance[0].state if attendance else 'absent',
                'check_in': attendance[0].check_in_time.strftime('%H:%M') if attendance and attendance[0].check_in_time else '',
                'check_out': attendance[0].check_out_time.strftime('%H:%M') if attendance and attendance[0].check_out_time else '',
            })
        
        # Create Excel file
        import io
        import xlsxwriter
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Attendance List')
        
        # Headers
        headers = ['Member', 'Registered Date', 'Attended', 'Check In', 'Check Out']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # Data
        for row, record in enumerate(data, 1):
            worksheet.write(row, 0, record['member'])
            worksheet.write(row, 1, record['registered'])
            worksheet.write(row, 2, record['attended'])
            worksheet.write(row, 3, record['check_in'])
            worksheet.write(row, 4, record['check_out'])
        
        workbook.close()
        output.seek(0)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'Attendance_{self.name}_{self.start_date.strftime("%Y-%m-%d")}.xlsx',
            'type': 'binary',
            'datas': output.read(),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
