# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfActivityRegistration(models.Model):
    _name = 'vf.activity.registration'
    _description = 'Activity Registration'
    _order = 'registration_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    schedule_id = fields.Many2one(
        'vf.activity.schedule',
        string='Activity Schedule',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        related='member_id.partner_id',
        store=True,
        readonly=True
    )
    
    # Registration details
    registration_date = fields.Datetime(
        string='Registration Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    notes = fields.Text(
        string='Notes',
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
        ('absent', 'Absent'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Approval
    approved_by = fields.Many2one(
        'res.partner',
        string='Approved By',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        tracking=True
    )
    
    # Attendance tracking
    attended = fields.Boolean(
        string='Attended',
        tracking=True
    )
    attendance_notes = fields.Text(
        string='Attendance Notes',
        tracking=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    _sql_constraints = [
        ('unique_schedule_member', 'unique(schedule_id, member_id)', 
         'Member can only register once per schedule!'),
    ]

    @api.depends('member_id', 'schedule_id')
    def _compute_display_name(self):
        for registration in self:
            if registration.member_id and registration.schedule_id:
                registration.display_name = f'{registration.member_id.name} - {registration.schedule_id.name}'
            else:
                registration.display_name = 'New Registration'

    @api.constrains('schedule_id', 'member_id')
    def _check_capacity(self):
        for registration in self:
            if registration.state == 'confirmed':
                schedule = registration.schedule_id
                if schedule.max_participants:
                    confirmed_count = self.search_count([
                        ('schedule_id', '=', schedule.id),
                        ('state', '=', 'confirmed')
                    ])
                    if confirmed_count > schedule.max_participants:
                        raise ValidationError(_('Activity is fully booked.'))

    def action_confirm(self):
        """Confirm the registration"""
        for registration in self:
            if registration.schedule_id.activity_id.require_approval:
                registration.write({
                    'state': 'confirmed',
                    'approved_by': self.env.user.partner_id.id,
                    'approval_date': fields.Datetime.now(),
                })
            else:
                registration.write({'state': 'confirmed'})
        return True

    def action_cancel(self):
        """Cancel the registration"""
        self.write({'state': 'cancelled'})
        return True

    def action_set_to_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True

    def action_mark_attended(self):
        """Mark as attended"""
        self.write({
            'state': 'attended',
            'attended': True
        })
        return True

    def action_mark_absent(self):
        """Mark as absent"""
        self.write({
            'state': 'absent',
            'attended': False
        })
        return True

    @api.model
    def create(self, vals):
        # Check if member can register
        member = self.env['vf.member'].browse(vals['member_id'])
        schedule = self.env['vf.activity.schedule'].browse(vals['schedule_id'])
        
        can_register, message = schedule.activity_id.can_register(member.partner_id)
        if not can_register:
            raise ValidationError(message)
        
        return super().create(vals)
