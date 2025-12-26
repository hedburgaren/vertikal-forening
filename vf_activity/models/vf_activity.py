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
    resource_ids = fields.Many2many(
        'vf.resource',
        'vf_activity_resource_rel',
        'activity_id',
        'resource_id',
        string='Resources',
        tracking=True
    )
    
    # Organization
    organizer_id = fields.Many2one(
        'res.partner',
        string='Organizer',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    section_id = fields.Many2one(
        'vf.section',
        string='Section',
        tracking=True
    )
    group_id = fields.Many2one(
        'vf.group',
        string='Group',
        tracking=True
    )
    
    # Registration
    allow_registration = fields.Boolean(
        string='Allow Registration',
        default=True,
        tracking=True
    )
    require_approval = fields.Boolean(
        string='Require Approval',
        default=False,
        tracking=True
    )
    max_participants = fields.Integer(
        string='Maximum Participants',
        tracking=True
    )
    registration_deadline = fields.Datetime(
        string='Registration Deadline',
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Visibility
    visibility = fields.Selection([
        ('public', 'Public'),
        ('members', 'Members Only'),
        ('participants', 'Participants Only'),
        ('custom', 'Custom'),
    ], string='Visibility', default='members', required=True, tracking=True)
    
    # Custom visibility
    allowed_member_ids = fields.Many2many(
        'vf.member',
        'vf_activity_member_rel',
        'activity_id',
        'member_id',
        string='Allowed Members',
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
    is_past = fields.Boolean(
        compute='_compute_is_past',
        string='Is Past'
    )
    
    # Relationships
    schedule_ids = fields.One2many(
        'vf.activity.schedule',
        'activity_id',
        string='Schedule'
    )
    document_ids = fields.Many2many(
        'vf.document',
        'vf_activity_document_rel',
        'activity_id',
        'document_id',
        string='Documents'
    )

    @api.depends('name', 'start_date')
    def _compute_display_name(self):
        for activity in self:
            if activity.start_date:
                date_str = activity.start_date.strftime('%Y-%m-%d')
                activity.display_name = f'{activity.name} ({date_str})'
            else:
                activity.display_name = activity.name

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for activity in self:
            if activity.start_date and activity.end_date:
                delta = activity.end_date - activity.start_date
                activity.duration = delta.total_seconds() / 3600.0
            else:
                activity.duration = 0

    @api.depends('schedule_ids.participant_count')
    def _compute_participant_count(self):
        for activity in self:
            activity.participant_count = sum(activity.schedule_ids.mapped('participant_count'))

    @api.depends('max_participants', 'participant_count')
    def _compute_available_spots(self):
        for activity in self:
            if activity.max_participants:
                activity.available_spots = activity.max_participants - activity.participant_count
            else:
                activity.available_spots = 0

    @api.depends('end_date')
    def _compute_is_past(self):
        for activity in self:
            activity.is_past = activity.end_date < fields.Datetime.now()

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for activity in self:
            if activity.start_date >= activity.end_date:
                raise ValidationError(_('End date must be after start date.'))

    @api.constrains('max_participants')
    def _check_max_participants(self):
        for activity in self:
            if activity.max_participants and activity.max_participants < 0:
                raise ValidationError(_('Maximum participants must be positive.'))

    @api.onchange('activity_type_id')
    def _onchange_activity_type(self):
        if self.activity_type_id:
            self.allow_registration = self.activity_type_id.allow_registration
            self.require_approval = self.activity_type_id.require_approval
            self.max_participants = self.activity_type_id.max_participants
            if not self.start_date and self.activity_type_id.default_duration:
                self.end_date = fields.Datetime.now() + timedelta(hours=self.activity_type_id.default_duration)

    def action_plan(self):
        """Set activity to planned"""
        self.write({'state': 'planned'})
        return True

    def action_confirm(self):
        """Confirm the activity"""
        self.write({'state': 'confirmed'})
        return True

    def action_start(self):
        """Start the activity"""
        self.write({'state': 'in_progress'})
        return True

    def action_complete(self):
        """Complete the activity"""
        self.write({'state': 'completed'})
        return True

    def action_cancel(self):
        """Cancel the activity"""
        self.write({'state': 'cancelled'})
        return True

    def action_set_to_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True

    def action_view_schedule(self):
        """View activity schedule"""
        self.ensure_one()
        return {
            'name': _('Activity Schedule'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.schedule',
            'view_mode': 'tree,form',
            'domain': [('activity_id', '=', self.id)],
            'context': {'default_activity_id': self.id},
        }

    def action_view_participants(self):
        """View all participants"""
        self.ensure_one()
        participants = []
        for schedule in self.schedule_ids:
            participants.extend(schedule.registration_ids.mapped('member_id'))
        
        if participants:
            return {
                'name': _('Activity Participants'),
                'type': 'ir.actions.act_window',
                'res_model': 'vf.member',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', participants.ids)],
                'context': {'form_view_initial_mode': 'readonly'},
            }
        else:
            self.message_post(
                body=_('No participants registered for this activity.'),
                message_type='notification'
            )
            return True

    def check_access(self, partner):
        """Check if partner can access this activity"""
        if self.visibility == 'public':
            return True
        
        if not partner.member_id and not partner.has_active_mandates:
            return False
        
        if self.visibility == 'members':
            return partner.member_id is not None or partner.has_active_mandates
        
        if self.visibility == 'participants':
            return partner.member_id in self.schedule_ids.mapped('registration_ids.member_id')
        
        if self.visibility == 'custom':
            return partner.member_id in self.allowed_member_ids
        
        return False

    def can_register(self, partner):
        """Check if partner can register for this activity"""
        if not self.allow_registration:
            return False, _('Registration is not allowed for this activity.')
        
        if self.state not in ['planned', 'confirmed']:
            return False, _('Registration is not open for this activity.')
        
        if self.is_past:
            return False, _('Cannot register for past activities.')
        
        if self.registration_deadline and self.registration_deadline < fields.Datetime.now():
            return False, _('Registration deadline has passed.')
        
        if self.max_participants and self.participant_count >= self.max_participants:
            return False, _('Activity is fully booked.')
        
        if not self.check_access(partner):
            return False, _('You do not have access to this activity.')
        
        return True, ''
