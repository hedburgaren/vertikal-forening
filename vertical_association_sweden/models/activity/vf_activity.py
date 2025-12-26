# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class VfActivity(models.Model):
    _name = 'vf.activity'
    _description = 'Association Activity'
    _order = 'start_date desc, name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Activity Name',
        required=True,
        tracking=True
    )
    description = fields.Html(
        string='Description',
        tracking=True
    )
    
    # Type and category
    activity_type_id = fields.Many2one(
        'vf.activity.type',
        string='Activity Type',
        required=True,
        tracking=True
    )
    
    # Scheduling
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
    
    # Location
    location = fields.Char(
        string='Location',
        tracking=True
    )
    location_id = fields.Many2one(
        'vf.resource',
        string='Resource',
        domain="[('resource_type', '=', 'location')]",
        tracking=True
    )
    
    # Organization
    organizer_id = fields.Many2one(
        'res.partner',
        string='Organizer',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    group_id = fields.Many2one(
        'vf.group',
        string='Organizing Group',
        tracking=True
    )
    
    # Registration settings
    allow_registration = fields.Boolean(
        string='Allow Registration',
        default=True,
        tracking=True
    )
    registration_start = fields.Datetime(
        string='Registration Start',
        tracking=True
    )
    registration_end = fields.Datetime(
        string='Registration End',
        tracking=True
    )
    max_participants = fields.Integer(
        string='Maximum Participants',
        tracking=True
    )
    require_approval = fields.Boolean(
        string='Require Approval',
        default=False,
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', required=True, tracking=True)
    
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
    waiting_list_count = fields.Integer(
        string='Waiting List',
        compute='_compute_waiting_list_count',
        store=True
    )
    is_full = fields.Boolean(
        string='Is Full',
        compute='_compute_is_full',
        store=True
    )
    can_register = fields.Boolean(
        string='Can Register',
        compute='_compute_can_register',
        store=True
    )
    
    # Relationships
    registration_ids = fields.One2many(
        'vf.activity.registration',
        'activity_id',
        string='Registrations'
    )
    attendance_ids = fields.One2many(
        'vf.activity.attendance',
        'activity_id',
        string='Attendance Records'
    )
    schedule_ids = fields.One2many(
        'vf.activity.schedule',
        'activity_id',
        string='Schedule'
    )
    
    # Color for calendar
    color = fields.Integer(
        related='activity_type_id.color',
        readonly=True
    )

    @api.depends('name', 'start_date')
    def _compute_display_name(self):
        for activity in self:
            if activity.start_date:
                activity.display_name = f'{activity.name} ({activity.start_date.strftime("%Y-%m-%d")})'
            else:
                activity.display_name = activity.name

    @api.depends('registration_ids.state')
    def _compute_participant_count(self):
        for activity in self:
            activity.participant_count = len(activity.registration_ids.filtered(
                lambda r: r.state == 'confirmed'
            ))

    @api.depends('registration_ids.state')
    def _compute_waiting_list_count(self):
        for activity in self:
            activity.waiting_list_count = len(activity.registration_ids.filtered(
                lambda r: r.state == 'waiting'
            ))

    @api.depends('participant_count', 'max_participants')
    def _compute_is_full(self):
        for activity in self:
            if activity.max_participants:
                activity.is_full = activity.participant_count >= activity.max_participants
            else:
                activity.is_full = False

    @api.depends('allow_registration', 'state', 'registration_start', 'registration_end', 'is_full')
    def _compute_can_register(self):
        now = fields.Datetime.now()
        for activity in self:
            activity.can_register = (
                activity.allow_registration and
                activity.state in ['planned', 'confirmed'] and
                not activity.is_full and
                (not activity.registration_start or activity.registration_start <= now) and
                (not activity.registration_end or activity.registration_end >= now)
            )

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for activity in self:
            if activity.start_date >= activity.end_date:
                raise ValidationError(_('Start date must be before end date.'))

    @api.constrains('registration_start', 'registration_end', 'start_date')
    def _check_registration_dates(self):
        for activity in self:
            if activity.registration_start and activity.registration_end:
                if activity.registration_start >= activity.registration_end:
                    raise ValidationError(_('Registration start must be before registration end.'))
            if activity.registration_end and activity.start_date:
                if activity.registration_end > activity.start_date:
                    raise ValidationError(_('Registration must end before activity starts.'))

    def action_confirm(self):
        """Confirm the activity"""
        self.write({'state': 'confirmed'})
        return True

    def action_cancel(self):
        """Cancel the activity"""
        self.write({'state': 'cancelled'})
        return True

    def action_complete(self):
        """Mark activity as completed"""
        self.write({'state': 'completed'})
        return True

    def action_view_registrations(self):
        """View all registrations"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_activity_registration_action').read()[0]
        action['domain'] = [('activity_id', '=', self.id)]
        return action

    def action_register_members(self):
        """Register members for this activity"""
        self.ensure_one()
        return {
            'name': _('Register Members'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.registration.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_activity_id': self.id},
        }

    def action_take_attendance(self):
        """Take attendance for this activity"""
        self.ensure_one()
        return {
            'name': _('Take Attendance'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.attendance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_activity_id': self.id},
        }

    @api.model
    def get_upcoming_activities(self, member_id=None, days=30):
        """Get upcoming activities"""
        date_limit = fields.Datetime.now() + timedelta(days=days)
        domain = [
            ('state', 'in', ['planned', 'confirmed']),
            ('start_date', '<=', date_limit),
            ('start_date', '>=', fields.Datetime.now()),
        ]
        
        if member_id:
            domain.append(('registration_ids.member_id', '=', member_id))
        
        return self.search(domain)

    def can_member_register(self, member_id):
        """Check if a member can register"""
        self.ensure_one()
        member = self.env['vf.member'].browse(member_id)
        
        if not self.can_register:
            return False, _('Registration is not open')
        
        if self.max_participants and self.participant_count >= self.max_participants:
            return False, _('Activity is full')
        
        # Check if already registered
        if self.registration_ids.filtered(lambda r: r.member_id.id == member_id):
            return False, _('Already registered')
        
        # Check age restrictions
        if self.activity_type_id.min_age and member.age < self.activity_type_id.min_age:
            return False, _('Member is too young')
        
        if self.activity_type_id.max_age and member.age > self.activity_type_id.max_age:
            return False, _('Member is too old')
        
        return True, _('Can register')
