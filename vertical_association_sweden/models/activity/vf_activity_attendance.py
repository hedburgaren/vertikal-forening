# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfActivityAttendance(models.Model):
    _name = 'vf.activity.attendance'
    _description = 'Activity Attendance'
    _order = 'schedule_id, partner_id'
    _rec_name = 'display_name'

    # Core fields
    schedule_id = fields.Many2one(
        'vf.activity.schedule',
        string='Activity Schedule',
        required=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Participant',
        required=True,
        domain=[('is_company', '=', False)]
    )
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        related='partner_id.member_id',
        store=True
    )
    
    # Attendance details
    check_in_time = fields.Datetime(
        string='Check In Time'
    )
    check_out_time = fields.Datetime(
        string='Check Out Time'
    )
    duration = fields.Float(
        compute='_compute_duration',
        string='Duration (hours)',
        store=True
    )
    
    # Status
    state = fields.Selection([
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ], string='Attendance Status', default='present', required=True)
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )
    
    # Recorded by
    recorded_by = fields.Many2one(
        'res.partner',
        string='Recorded By',
        default=lambda self: self.env.user.partner_id,
        domain=[('is_company', '=', False)]
    )
    recording_date = fields.Datetime(
        string='Recording Date',
        default=fields.Datetime.now
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('partner_id', 'schedule_id')
    def _compute_display_name(self):
        for attendance in self:
            if attendance.partner_id and attendance.schedule_id:
                attendance.display_name = f'{attendance.partner_id.name} - {attendance.schedule_id.name}'
            else:
                attendance.display_name = 'Attendance Record'

    @api.depends('check_in_time', 'check_out_time')
    def _compute_duration(self):
        for attendance in self:
            if attendance.check_in_time and attendance.check_out_time:
                delta = attendance.check_out_time - attendance.check_in_time
                attendance.duration = delta.total_seconds() / 3600.0
            else:
                attendance.duration = 0

    @api.constrains('check_in_time', 'check_out_time')
    def _check_times(self):
        for attendance in self:
            if attendance.check_in_time and attendance.check_out_time:
                if attendance.check_in_time >= attendance.check_out_time:
                    raise ValidationError(_('Check out time must be after check in time.'))
            
            # Check that times are within schedule
            if attendance.check_in_time:
                schedule = attendance.schedule_id
                if attendance.check_in_time < schedule.start_date:
                    raise ValidationError(_('Check in time cannot be before the activity starts.'))
                if schedule.end_date and attendance.check_in_time > schedule.end_date:
                    raise ValidationError(_('Check in time cannot be after the activity ends.'))

    def action_check_in(self):
        """Check in participant"""
        self.write({
            'check_in_time': fields.Datetime.now(),
            'state': 'present',
        })
        return True

    def action_check_out(self):
        """Check out participant"""
        self.write({
            'check_out_time': fields.Datetime.now(),
        })
        return True

    def action_mark_present(self):
        """Mark as present"""
        self.write({'state': 'present'})
        return True

    def action_mark_absent(self):
        """Mark as absent"""
        self.write({'state': 'absent'})
        return True

    def action_mark_late(self):
        """Mark as late"""
        self.write({'state': 'late'})
        return True

    def action_mark_excused(self):
        """Mark as excused"""
        self.write({'state': 'excused'})
        return True
