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
            raise ValidationError(_('Registration is not allowed for this activity.'))
        
        # Check if member can register
        can_register, message = activity.can_member_register(member.partner_id.id)
        if not can_register:
            raise ValidationError(message)
        
        # Check if already registered
        existing = self.search([
            ('schedule_id', 'in', activity.schedule_ids.ids),
            ('member_id', '=', member_id)
        ])
        if existing:
            raise ValidationError(_('Already registered for this activity.'))
        
        # Create registration
        registration = self.create({
            'schedule_id': activity.schedule_ids[0].id if activity.schedule_ids else False,
            'member_id': member_id,
            'notes': notes,
            'registered_via_portal': True,
            'portal_notes': notes,
        })
        
        # Send confirmation
        registration._send_confirmation_email()
        
        return registration

    def _send_confirmation_email(self):
        """Send registration confirmation email"""
        self.ensure_one()
        
        template = self.env.ref('vertical_association_sweden.email_template_activity_registration')
        if template:
            template.send_mail(self.id, force_send=True)
            self.write({
                'confirmation_sent': True,
                'confirmation_date': fields.Datetime.now(),
            })

    def action_cancel_via_portal(self):
        """Cancel registration via portal"""
        self.ensure_one()
        
        # Check if cancellation is allowed
        if self.state in ['attended', 'absent']:
            raise UserError(_('Cannot cancel a completed registration.'))
        
        # Check cancellation deadline
        if self.schedule_id.start_date:
            deadline = self.schedule_id.start_date - timedelta(days=1)
            if fields.Datetime.now() > deadline:
                raise UserError(_('Cancellation deadline has passed.'))
        
        self.write({'state': 'cancelled'})
        
        # Send cancellation email
        template = self.env.ref('vertical_association_sweden.email_template_activity_cancellation')
        if template:
            template.send_mail(self.id, force_send=True)
        
        return True

    @api.model
    def get_upcoming_activities(self, member_id):
        """Get upcoming activities for a member"""
        member = self.env['vf.member'].browse(member_id)
        
        # Get activities member can register for
        activities = self.env['vf.activity'].get_upcoming_activities(member_id)
        
        # Filter out already registered activities
        registered_activities = self.search([
            ('member_id', '=', member_id),
            ('state', '!=', 'cancelled')
        ]).mapped('schedule_id.activity_id')
        
        available_activities = activities - registered_activities
        
        return [{
            'id': activity.id,
            'name': activity.name,
            'start_date': activity.start_date,
            'end_date': activity.end_date,
            'location': activity.location,
            'can_register': activity.can_register,
            'participant_count': activity.participant_count,
            'max_participants': activity.max_participants,
        } for activity in available_activities]

    @api.model
    def get_my_registrations(self, member_id):
        """Get member's activity registrations"""
        registrations = self.search([
            ('member_id', '=', member_id)
        ])
        
        return [{
            'id': reg.id,
            'activity_name': reg.schedule_id.activity_id.name,
            'start_date': reg.schedule_id.start_date,
            'end_date': reg.schedule_id.end_date,
            'location': reg.schedule_id.activity_id.location,
            'state': reg.state,
            'registration_date': reg.registration_date,
            'can_cancel': reg._can_cancel(),
        } for reg in registrations]

    def _can_cancel(self):
        """Check if registration can be cancelled"""
        if self.state in ['attended', 'absent', 'cancelled']:
            return False
        
        if self.schedule_id.start_date:
            deadline = self.schedule_id.start_date - timedelta(days=1)
            return fields.Datetime.now() <= deadline
        
        return True
