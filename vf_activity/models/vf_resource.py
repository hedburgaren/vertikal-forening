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
    
    # Availability
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    requires_approval = fields.Boolean(
        string='Requires Approval',
        default=False,
        tracking=True,
        help='Resource booking requires approval'
    )
    
    # Booking rules
    min_booking_duration = fields.Float(
        string='Minimum Booking Duration (hours)',
        default=0.5,
        tracking=True
    )
    max_booking_duration = fields.Float(
        string='Maximum Booking Duration (hours)',
        default=24.0,
        tracking=True
    )
    advance_booking_days = fields.Integer(
        string='Advance Booking Days',
        default=365,
        tracking=True,
        help='Maximum days in advance the resource can be booked'
    )
    
    # Responsible person
    manager_id = fields.Many2one(
        'res.partner',
        string='Resource Manager',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Computed fields
    current_bookings = fields.Integer(
        compute='_compute_current_bookings',
        string='Current Bookings'
    )
    is_available = fields.Boolean(
        compute='_compute_is_available',
        string='Is Available'
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
    ]

    @api.depends('resource_ids')
    def _compute_current_bookings(self):
        for resource in self:
            now = fields.Datetime.now()
            resource.current_bookings = self.env['vf.activity.schedule'].search_count([
                ('resource_ids', 'in', [resource.id]),
                ('start_date', '<=', now),
                ('end_date', '>=', now),
                ('state', '!=', 'cancelled')
            ])

    @api.depends('current_bookings', 'active')
    def _compute_is_available(self):
        for resource in self:
            resource.is_available = resource.active and resource.current_bookings == 0

    @api.constrains('capacity')
    def _check_capacity(self):
        for resource in self:
            if resource.capacity and resource.capacity < 0:
                raise ValidationError(_('Capacity must be positive.'))

    @api.constrains('min_booking_duration', 'max_booking_duration')
    def _check_booking_duration(self):
        for resource in self:
            if resource.min_booking_duration <= 0:
                raise ValidationError(_('Minimum booking duration must be positive.'))
            if resource.max_booking_duration <= 0:
                raise ValidationError(_('Maximum booking duration must be positive.'))
            if resource.min_booking_duration > resource.max_booking_duration:
                raise ValidationError(_('Minimum booking duration cannot be greater than maximum.'))

    def action_view_bookings(self):
        """View all bookings for this resource"""
        self.ensure_one()
        return {
            'name': _('Resource Bookings'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.activity.schedule',
            'view_mode': 'tree,form',
            'domain': [('resource_ids', 'in', [self.id])],
            'context': {
                'default_resource_ids': [(4, self.id)],
            },
        }

    def check_availability(self, start_date, end_date, exclude_schedule=None):
        """Check if resource is available for the given period"""
        if not self.active:
            return False, _('Resource is not active.')
        
        # Check booking duration constraints
        duration = (end_date - start_date).total_seconds() / 3600.0
        if duration < self.min_booking_duration:
            return False, _('Minimum booking duration is %s hours.') % self.min_booking_duration
        if duration > self.max_booking_duration:
            return False, _('Maximum booking duration is %s hours.') % self.max_booking_duration
        
        # Check advance booking constraint
        days_ahead = (start_date - fields.Datetime.now()).days
        if days_ahead > self.advance_booking_days:
            return False, _('Resource can only be booked %s days in advance.') % self.advance_booking_days
        
        # Check for conflicting bookings
        domain = [
            ('resource_ids', 'in', [self.id]),
            ('state', '!=', 'cancelled'),
            '|',
            '&', ('start_date', '<=', start_date), ('end_date', '>', start_date),
            '&', ('start_date', '<', end_date), ('end_date', '>=', end_date),
            '&', ('start_date', '>=', start_date), ('end_date', '<=', end_date),
        ]
        
        if exclude_schedule:
            domain.append(('id', '!=', exclude_schedule.id))
        
        conflicts = self.env['vf.activity.schedule'].search(domain)
        if conflicts:
            conflict_times = ', '.join([
                f'{c.start_date.strftime("%Y-%m-%d %H:%M")} - {c.end_date.strftime("%Y-%m-%d %H:%M")}'
                for c in conflicts[:3]
            ])
            return False, _('Resource is already booked during: %s') % conflict_times
        
        return True, ''
