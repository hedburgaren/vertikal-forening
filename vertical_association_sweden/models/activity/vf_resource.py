# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfResource(models.Model):
    _name = 'vf.resource'
    _description = 'Activity Resource'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Resource Name',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        help='Unique code for resource identification'
    )
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    # Resource type
    resource_type = fields.Selection([
        ('room', 'Room'),
        ('equipment', 'Equipment'),
        ('vehicle', 'Vehicle'),
        ('facility', 'Facility'),
        ('other', 'Other'),
    ], string='Resource Type', required=True, tracking=True)
    
    # Location
    location = fields.Char(
        string='Location',
        tracking=True,
        help='Physical location of the resource'
    )
    
    # Capacity
    capacity = fields.Integer(
        string='Capacity',
        tracking=True,
        help='Maximum number of people this resource can accommodate'
    )
    
    # Status
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    available = fields.Boolean(
        string='Available',
        default=True,
        tracking=True,
        help='Resource is currently available for booking'
    )
    
    # Booking settings
    requires_approval = fields.Boolean(
        string='Requires Approval',
        default=False,
        tracking=True,
        help='Booking this resource requires approval'
    )
    max_booking_duration = fields.Float(
        string='Max Booking Duration (hours)',
        tracking=True,
        help='Maximum duration for a single booking'
    )
    
    # Computed fields
    booking_count = fields.Integer(
        string='Active Bookings',
        compute='_compute_booking_count',
        store=True
    )
    
    # Relationships
    booking_ids = fields.One2many(
        'vf.resource.booking',
        'resource_id',
        string='Bookings'
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Resource code must be unique!'),
    ]

    @api.depends('booking_ids.state')
    def _compute_booking_count(self):
        for resource in self:
            resource.booking_count = len(resource.booking_ids.filtered(
                lambda b: b.state == 'confirmed'
            ))

    def action_view_bookings(self):
        """View all bookings for this resource"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_resource_booking_action').read()[0]
        action['domain'] = [('resource_id', '=', self.id)]
        return action

    def action_book(self):
        """Book this resource"""
        self.ensure_one()
        return {
            'name': _('Book Resource'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.resource.booking',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_resource_id': self.id},
        }

    def check_availability(self, start_date, end_date):
        """Check if resource is available for the given period"""
        self.ensure_one()
        
        if not self.active or not self.available:
            return False, _('Resource not available')
        
        # Check for overlapping bookings
        overlapping = self.env['vf.resource.booking'].search([
            ('resource_id', '=', self.id),
            ('state', '=', 'confirmed'),
            '|', ('start_date', '<', end_date),
                 ('end_date', '>', start_date),
        ])
        
        if overlapping:
            return False, _('Resource already booked for this period')
        
        # Check booking duration
        if self.max_booking_duration:
            duration = (end_date - start_date).total_seconds() / 3600.0
            if duration > self.max_booking_duration:
                return False, _('Booking exceeds maximum duration')
        
        return True, _('Available')


class VfResourceBooking(models.Model):
    _name = 'vf.resource.booking'
    _description = 'Resource Booking'
    _order = 'start_date'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    resource_id = fields.Many2one(
        'vf.resource',
        string='Resource',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    activity_id = fields.Many2one(
        'vf.activity',
        string='Activity',
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Booked By',
        required=True,
        tracking=True,
        domain=[('is_company', '=', False)]
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
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Notes
    notes = fields.Text(
        string='Notes',
        tracking=True
    )
    
    # Approval
    approved_by = fields.Many2one(
        'res.partner',
        string='Approved By',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        readonly=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('resource_id', 'start_date')
    def _compute_display_name(self):
        for booking in self:
            if booking.resource_id and booking.start_date:
                booking.display_name = f'{booking.resource_id.name} - {booking.start_date.strftime("%Y-%m-%d %H:%M")}'
            else:
                booking.display_name = 'New Booking'

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for booking in self:
            if booking.start_date >= booking.end_date:
                raise ValidationError(_('Start date must be before end date.'))

    @api.constrains('resource_id', 'start_date', 'end_date')
    def _check_availability(self):
        for booking in self:
            if booking.state == 'confirmed':
                available, message = booking.resource_id.check_availability(
                    booking.start_date,
                    booking.end_date
                )
                if not available:
                    raise ValidationError(message)

    def action_confirm(self):
        """Confirm the booking"""
        for booking in self:
            if booking.resource_id.requires_approval:
                booking.write({
                    'state': 'confirmed',
                    'approved_by': self.env.user.partner_id.id,
                    'approval_date': fields.Datetime.now(),
                })
            else:
                booking.write({'state': 'confirmed'})
        return True

    def action_cancel(self):
        """Cancel the booking"""
        self.write({'state': 'cancelled'})
        return True
