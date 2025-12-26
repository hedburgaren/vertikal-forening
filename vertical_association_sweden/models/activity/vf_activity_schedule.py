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
        ('yearly', 'Yearly'),
    ], string='Recurrence Type')
    recurrence_interval = fields.Integer(
        string='Interval',
        default=1,
        help='Repeat every X days/weeks/months/years'
    )
    recurrence_end = fields.Date(
        string='Recurrence End',
        help='End date for recurrence'
    )
    
    # Location
    location = fields.Char(
        string='Location',
        tracking=True
    )
    resource_id = fields.Many2one(
        'vf.resource',
        string='Resource',
        tracking=True
    )
    
    # Registration
    max_participants = fields.Integer(
        string='Maximum Participants',
        tracking=True
    )
    allow_registration = fields.Boolean(
        string='Allow Registration',
        default=True,
        tracking=True
    )
    
    # Status
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    participant_count = fields.Integer(
        string='Participants',
        compute='_compute_participant_count',
        store=True
    )
    is_full = fields.Boolean(
        string='Is Full',
        compute='_compute_is_full',
        store=True
    )
    
    # Relationships
    registration_ids = fields.One2many(
        'vf.activity.registration',
        'schedule_id',
        string='Registrations'
    )

    @api.depends('name', 'start_date')
    def _compute_display_name(self):
        for schedule in self:
            if schedule.start_date:
                schedule.display_name = f'{schedule.name} ({schedule.start_date.strftime("%Y-%m-%d %H:%M")})'
            else:
                schedule.display_name = schedule.name

    @api.depends('registration_ids.state')
    def _compute_participant_count(self):
        for schedule in self:
            schedule.participant_count = len(schedule.registration_ids.filtered(
                lambda r: r.state == 'confirmed'
            ))

    @api.depends('participant_count', 'max_participants')
    def _compute_is_full(self):
        for schedule in self:
            if schedule.max_participants:
                schedule.is_full = schedule.participant_count >= schedule.max_participants
            else:
                schedule.is_full = False

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for schedule in self:
            if schedule.start_date >= schedule.end_date:
                raise ValidationError(_('Start date must be before end date.'))

    @api.constrains('recurrence_interval')
    def _check_recurrence_interval(self):
        for schedule in self:
            if schedule.is_recurring and schedule.recurrence_interval <= 0:
                raise ValidationError(_('Recurrence interval must be greater than 0.'))

    def action_generate_occurrences(self):
        """Generate recurring schedule occurrences"""
        self.ensure_one()
        if not self.is_recurring:
            raise ValidationError(_('This is not a recurring schedule.'))
        
        from datetime import datetime, timedelta
        
        occurrences = []
        current_date = self.start_date.date()
        end_date = self.recurrence_end or self.start_date.date() + timedelta(days=365)
        
        while current_date <= end_date:
            # Create occurrence
            occurrence_start = datetime.combine(current_date, self.start_date.time())
            occurrence_end = datetime.combine(current_date, self.end_date.time())
            
            # Check if already exists
            existing = self.search([
                ('activity_id', '=', self.activity_id.id),
                ('start_date', '=', occurrence_start),
                ('end_date', '=', occurrence_end),
                ('id', '!=', self.id)
            ])
            
            if not existing:
                self.env['vf.activity.schedule'].create({
                    'name': f'{self.name} - {current_date}',
                    'activity_id': self.activity_id.id,
                    'start_date': occurrence_start,
                    'end_date': occurrence_end,
                    'all_day': self.all_day,
                    'location': self.location,
                    'resource_id': self.resource_id.id,
                    'max_participants': self.max_participants,
                    'allow_registration': self.allow_registration,
                })
                occurrences.append(current_date)
            
            # Move to next occurrence
            if self.recurrence_type == 'daily':
                current_date += timedelta(days=self.recurrence_interval)
            elif self.recurrence_type == 'weekly':
                current_date += timedelta(weeks=self.recurrence_interval)
            elif self.recurrence_type == 'monthly':
                # Add months
                month = current_date.month - 1 + self.recurrence_interval
                year = current_date.year + month // 12
                month = month % 12 + 1
                current_date = current_date.replace(year=year, month=month)
            elif self.recurrence_type == 'yearly':
                current_date = current_date.replace(year=current_date.year + self.recurrence_interval)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Occurrences Generated'),
                'message': _('%d schedule occurrences have been generated.' % len(occurrences)),
                'type': 'success',
            }
        }

    def action_view_registrations(self):
        """View registrations for this schedule"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_activity_registration_action').read()[0]
        action['domain'] = [('schedule_id', '=', self.id)]
        return action

    def can_member_register(self, member_id):
        """Check if a member can register"""
        self.ensure_one()
        
        if not self.allow_registration:
            return False, _('Registration not allowed')
        
        if self.max_participants and self.participant_count >= self.max_participants:
            return False, _('Schedule is full')
        
        # Check if already registered
        if self.registration_ids.filtered(lambda r: r.member_id.id == member_id):
            return False, _('Already registered')
        
        return True, _('Can register')
