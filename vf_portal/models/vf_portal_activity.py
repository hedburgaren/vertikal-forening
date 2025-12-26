# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class VfPortalActivity(models.Model):
    _name = 'vf.portal.activity'
    _description = 'Portal Activity Registration'
    _inherit = ['vf.activity.registration']

    # Portal specific fields
    registered_via_portal = fields.Boolean(
        string='Registered via Portal',
        default=True
    )
    portal_notes = fields.Text(
        string='Portal Notes',
        help='Notes added by member during registration'
    )
    
    # Registration confirmation
    confirmation_sent = fields.Boolean(
        string='Confirmation Sent',
        readonly=True
    )
    confirmation_date = fields.Datetime(
        string='Confirmation Date',
        readonly=True
    )
    
    # Waiting list
    waiting_list_position = fields.Integer(
        string='Waiting List Position',
        readonly=True
    )
    auto_register_if_available = fields.Boolean(
        string='Auto-Register if Available',
        default=False,
        help='Automatically register if a spot becomes available'
    )

    @api.model
    def portal_register(self, activity_id, member_id, notes=None):
        """Register member for activity via portal"""
        activity = self.env['vf.activity'].browse(activity_id)
        member = self.env['vf.member'].browse(member_id)
        
        # Check if registration is allowed
        if not activity.allow_registration:
            raise UserError(_('Registration is not allowed for this activity.'))
        
        # Check if already registered
        existing = self.search([
            ('schedule_id.activity_id', '=', activity_id),
            ('member_id', '=', member_id)
        ])
        if existing:
            raise UserError(_('You are already registered for this activity.'))
        
        # Find available schedule
        schedule = self._find_available_schedule(activity, member)
        
        if not schedule:
            # Add to waiting list
            waiting_list = self.env['vf.activity.waiting.list'].create({
                'activity_id': activity_id,
                'member_id': member_id,
                'notes': notes,
            })
            
            return {
                'success': False,
                'message': _('Activity is full. You have been added to the waiting list.'),
                'waiting_list_position': waiting_list.position,
            }
        
        # Create registration
        registration = self.create({
            'schedule_id': schedule.id,
            'member_id': member_id,
            'notes': notes,
            'state': 'confirmed' if not activity.require_approval else 'draft',
        })
        
        # Send confirmation
        registration._send_confirmation_email()
        
        return {
            'success': True,
            'registration_id': registration.id,
            'message': _('Registration successful!') if not activity.require_approval else _('Registration submitted for approval.'),
        }

    def _find_available_schedule(self, activity, member):
        """Find an available schedule for the activity"""
        for schedule in activity.schedule_ids:
            # Check capacity
            if schedule.max_participants and schedule.registered_count >= schedule.max_participants:
                continue
            
            # Check age requirements
            if schedule.min_age and member.age < schedule.min_age:
                continue
            if schedule.max_age and member.age > schedule.max_age:
                continue
            
            # Check group requirements
            if schedule.group_id and schedule.group_id not in member.group_membership_ids.mapped('group_id'):
                continue
            
            return schedule
        
        return False

    def _send_confirmation_email(self):
        """Send registration confirmation email"""
        self.ensure_one()
        
        template = self.env.ref('vf_portal.email_template_activity_confirmation')
        template.send_mail(self.id)
        
        self.write({
            'confirmation_sent': True,
            'confirmation_date': fields.Datetime.now(),
        })

    def action_cancel_via_portal(self):
        """Cancel registration via portal"""
        self.ensure_one()
        
        # Check if cancellation is allowed
        activity = self.schedule_id.activity_id
        if activity.start_date <= fields.Datetime.now():
            raise UserError(_('Cannot cancel registration for activities that have already started.'))
        
        # Check cancellation deadline
        if activity.registration_deadline and fields.Datetime.now() > activity.registration_deadline:
            raise UserError(_('Registration cancellation deadline has passed.'))
        
        # Cancel registration
        self.state = 'cancelled'
        
        # Notify if on waiting list
        if self.waiting_list_position:
            self._notify_waiting_list()
        
        # Send cancellation email
        template = self.env.ref('vf_portal.email_template_activity_cancellation')
        template.send_mail(self.id)
        
        return True

    def _notify_waiting_list(self):
        """Notify next person on waiting list"""
        waiting_list = self.env['vf.activity.waiting.list'].search([
            ('activity_id', '=', self.schedule_id.activity_id.id),
            ('position', '=', 1)
        ], limit=1)
        
        if waiting_list and waiting_list.auto_register_if_available:
            # Try to register automatically
            result = self.portal_register(
                waiting_list.activity_id.id,
                waiting_list.member_id.id
            )
            
            if result.get('success'):
                waiting_list.unlink()

    def action_view_activity_details(self):
        """View activity details"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Activity Details',
            'res_model': 'vf.activity',
            'res_id': self.schedule_id.activity_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'form_view_initial_mode': 'readonly',
            },
        }


class VfActivityWaitingList(models.Model):
    _name = 'vf.activity.waiting.list'
    _description = 'Activity Waiting List'
    _order = 'position, date_added'

    activity_id = fields.Many2one(
        'vf.activity',
        string='Activity',
        required=True,
        ondelete='cascade'
    )
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        ondelete='cascade'
    )
    date_added = fields.Datetime(
        string='Date Added',
        required=True,
        default=fields.Datetime.now
    )
    position = fields.Integer(
        string='Position',
        compute='_compute_position',
        store=True
    )
    notes = fields.Text(
        string='Notes'
    )
    auto_register_if_available = fields.Boolean(
        string='Auto-Register if Available',
        default=False
    )
    
    _sql_constraints = [
        ('unique_activity_member', 'unique(activity_id, member_id)', 
         'Member can only be on waiting list once per activity!'),
    ]

    @api.depends('activity_id', 'date_added')
    def _compute_position(self):
        for record in self:
            position = self.search_count([
                ('activity_id', '=', record.activity_id.id),
                ('date_added', '<=', record.date_added)
            ])
            record.position = position
