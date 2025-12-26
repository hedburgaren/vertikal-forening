# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfActivitySchedule(models.Model):
    _name = 'vf.activity.schedule'
    _description = 'Activity Schedule'
    _order = 'start_date, name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Schedule Name',
        required=True,
        tracking=True
    )
    activity_id = fields.Many2one(
        'vf.activity',
        string='Activity',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Timing
    start_date = fields.Datetime(
        string='Start Date',
        required=True,
        tracking=True
    )
    end_date = fields.Datetime(
        string='End Date',
        required=True,
        tracking=True
    )
    all_day = fields.Boolean(
        string='All Day',
        default=False,
        tracking=True
    )
    
    # Recurrence
    is_recurring = fields.Boolean(
        string='Is Recurring',
        default=False,
        tracking=True
    )
    recurrence_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Recurrence Type', tracking=True)
    recurrence_interval = fields.Integer(
        string='Interval',
        default=1,
        tracking=True,
        help='Repeat every X days/weeks/months'
    )
    recurrence_end_date = fields.Date(
        string='Recurrence End Date',
        tracking=True
    )
    
    # Staff
    instructor_id = fields.Many2one(
        'res.partner',
        string='Instructor',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    assistant_ids = fields.Many2many(
        'res.partner',
        'vf_schedule_assistant_rel',
        'schedule_id',
        'partner_id',
        string='Assistants',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Capacity
    max_participants = fields.Integer(
        string='Maximum Participants',
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Notes
    notes = fields.Text(
        string='Notes',
        tracking=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    duration = fields.Float(
        compute='_compute_duration',
        string='Duration (hours)',
        store=True
    )
    participant_count = fields.Integer(
        compute='_compute_participant_count',
        string='Participants'
    )
    available_spots = fields.Integer(
        compute='_compute_available_spots',
        string='Available Spots'
    )
    
    # Relationships
    registration_ids = fields.One2many(
        'vf.activity.registration',
        'schedule_id',
        string='Registrations'
    )
    attendance_ids = fields.One2many(
        'vf.activity.attendance',
        'schedule_id',
        string='Attendance Records'
    )

    @api.depends('name', 'start_date')
    def _compute_display_name(self):
        for schedule in self:
            if schedule.start_date:
                date_str = schedule.start_date.strftime('%Y-%m-%d %H:%M')
                schedule.display_name = f'{schedule.name} ({date_str})'
            else:
                schedule.display_name = schedule.name

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for schedule in self:
            if schedule.start_date and schedule.end_date:
                delta = schedule.end_date - schedule.start_date
                schedule.duration = delta.total_seconds() / 3600.0
            else:
                schedule.duration = 0

    @api.depends('registration_ids.state')
    def _compute_participant_count(self):
        for schedule in self:
            schedule.participant_count = len(
                schedule.registration_ids.filtered(lambda r: r.state == 'confirmed')
            )

    @api.depends('max_participants', 'participant_count')
    def _compute_available_spots(self):
        for schedule in self:
            if schedule.max_participants:
                schedule.available_spots = schedule.max_participants - schedule.participant_count
            else:
                schedule.available_spots = 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for schedule in self:
            if schedule.start_date >= schedule.end_date:
                raise ValidationError(_('End date must be after start date.'))

    @api.constrains('max_participants')
    def _check_max_participants(self):
        for schedule in self:
            if schedule.max_participants and schedule.max_participants < 0:
                raise ValidationError(_('Maximum participants must be positive.'))

    @api.constrains('is_recurring', 'recurrence_type', 'recurrence_interval')
    def _check_recurrence(self):
        for schedule in self:
            if schedule.is_recurring:
                if not schedule.recurrence_type:
                    raise ValidationError(_('Recurrence type is required for recurring schedules.'))
                if schedule.recurrence_interval <= 0:
                    raise ValidationError(_('Recurrence interval must be positive.'))

    @api.onchange('activity_id')
    def _onchange_activity(self):
        if self.activity_id:
            if not self.max_participants:
                self.max_participants = self.activity_id.max_participants

    def action_plan(self):
        """Set schedule to planned"""
        self.write({'state': 'planned'})
        return True

    def action_confirm(self):
        """Confirm the schedule"""
        self.write({'state': 'confirmed'})
        return True

    def action_complete(self):
        """Complete the schedule"""
        self.write({'state': 'completed'})
        return True

    def action_cancel(self):
        """Cancel the schedule"""
        self.write({'state': 'cancelled'})
        return True

    def action_set_to_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True

    def action_view_registrations(self):
        """View registrations"""
        self.ensure_one()
        return {
            'name': _('Registrations'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.registration',
            'view_mode': 'tree,form',
            'domain': [('schedule_id', '=', self.id)],
            'context': {'default_schedule_id': self.id},
        }

    def action_take_attendance(self):
        """Open attendance wizard"""
        self.ensure_one()
        return {
            'name': _('Take Attendance'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_schedule_id': self.id},
        }

    def generate_recurrences(self):
        """Generate recurring schedules"""
        self.ensure_one()
        
        if not self.is_recurring:
            return True
        
        recurrences = []
        current_date = self.start_date
        end_date = fields.Date.to_datetime(self.recurrence_end_date) if self.recurrence_end_date else None
        
        while True:
            # Calculate next occurrence
            if self.recurrence_type == 'daily':
                current_date += timedelta(days=self.recurrence_interval)
            elif self.recurrence_type == 'weekly':
                current_date += timedelta(weeks=self.recurrence_interval)
            elif self.recurrence_type == 'monthly':
                current_date += timedelta(days=30 * self.recurrence_interval)  # Simplified
            
            # Check if we've reached the end date
            if end_date and current_date.date() > end_date.date():
                break
            
            # Calculate end time
            duration = self.end_date - self.start_date
            new_end_date = current_date + duration
            
            # Create recurrence
            recurrences.append({
                'name': self.name,
                'activity_id': self.activity_id.id,
                'start_date': current_date,
                'end_date': new_end_date,
                'all_day': self.all_day,
                'is_recurring': False,  # Recurrences are not recurring themselves
                'instructor_id': self.instructor_id.id,
                'assistant_ids': [(6, 0, self.assistant_ids.ids)],
                'max_participants': self.max_participants,
                'state': 'draft',
                'notes': self.notes,
            })
            
            # Limit to reasonable number
            if len(recurrences) >= 52:  # Max 1 year of weekly recurrences
                break
        
        # Create all recurrences
        if recurrences:
            self.env['vf.activity.schedule'].create(recurrences)
        
        return True
