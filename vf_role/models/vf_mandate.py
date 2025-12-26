# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class VfMandate(models.Model):
    _name = 'vf.mandate'
    _description = 'Position Mandate'
    _order = 'position_id, start_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    person_id = fields.Many2one(
        'res.partner',
        string='Person',
        required=True,
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    position_id = fields.Many2one(
        'vf.position',
        string='Position',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Time management
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True
    )
    
    # Status and appointment
    status = fields.Selection([
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked'),
    ], string='Status', default='pending', required=True, tracking=True)
    
    appointed_by = fields.Many2one(
        'res.partner',
        string='Appointed By',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    appointment_date = fields.Date(
        string='Appointment Date',
        tracking=True
    )
    
    # Administrative
    notes = fields.Text(
        string='Notes',
        tracking=True,
        groups='vf_base.vf_admin'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    days_remaining = fields.Integer(
        compute='_compute_days_remaining',
        search='_search_days_remaining'
    )
    is_expiring_soon = fields.Boolean(
        compute='_compute_is_expiring_soon',
        store=True
    )
    
    # Relationships
    extension_ids = fields.One2many(
        'vf.mandate.extension',
        'mandate_id',
        string='Extensions'
    )

    @api.depends('person_id', 'position_id')
    def _compute_display_name(self):
        for mandate in self:
            mandate.display_name = f'{mandate.person_id.name} - {mandate.position_id.display_name}'

    @api.depends('end_date', 'status')
    def _compute_days_remaining(self):
        today = date.today()
        for mandate in self:
            if mandate.status == 'active' and mandate.end_date:
                mandate.days_remaining = (mandate.end_date - today).days
            else:
                mandate.days_remaining = 0

    @api.depends('days_remaining', 'status')
    def _compute_is_expiring_soon(self):
        for mandate in self:
            if mandate.status == 'active':
                mandate.is_expiring_soon = (
                    0 <= mandate.days_remaining <= 30
                )
            else:
                mandate.is_expiring_soon = False

    def _search_days_remaining(self, operator, value):
        """Search mandates by days remaining"""
        if operator not in ('=', '!=', '<', '<=', '>', '>='):
            raise UserError(_('Invalid operator for days remaining search'))
        
        today = date.today()
        if operator == '<=':
            target_date = today + timedelta(days=value)
            return [
                ('status', '=', 'active'),
                ('end_date', '<=', target_date)
            ]
        elif operator == '>':
            target_date = today + timedelta(days=value)
            return [
                ('status', '=', 'active'),
                ('end_date', '>', target_date)
            ]
        # Add more operators as needed
        return []

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for mandate in self:
            if mandate.start_date >= mandate.end_date:
                raise ValidationError(_('End date must be after start date.'))

    @api.constrains('person_id', 'position_id', 'start_date', 'end_date')
    def _check_no_overlap(self):
        """Check for overlapping mandates"""
        for mandate in self:
            overlapping = self.search([
                ('id', '!=', mandate.id),
                ('person_id', '=', mandate.person_id.id),
                ('position_id', '=', mandate.position_id.id),
                ('status', 'in', ['active', 'pending']),
                '|',
                '&', ('start_date', '<=', mandate.start_date),
                     ('end_date', '>=', mandate.start_date),
                '&', ('start_date', '<=', mandate.end_date),
                     ('end_date', '>=', mandate.end_date),
            ])
            if overlapping:
                raise ValidationError(_(
                    'This person already has a mandate for this position during this period.'
                ))

    @api.model
    def update_expired_mandates(self):
        """Cron job to update expired mandates"""
        today = date.today()
        expired = self.search([
            ('status', '=', 'active'),
            ('end_date', '<', today)
        ])
        expired.write({'status': 'expired'})
        return True

    @api.model
    def send_expiry_reminders(self):
        """Cron job to send reminders for expiring mandates"""
        # Send reminders 30 days before expiry
        reminder_date = date.today() + timedelta(days=30)
        expiring = self.search([
            ('status', '=', 'active'),
            ('end_date', '=', reminder_date)
        ])
        
        template = self.env.ref('vf_role.email_template_mandate_expiry')
        for mandate in expiring:
            template.send_mail(mandate.id)
        
        return True

    def action_activate(self):
        """Activate the mandate"""
        self.write({
            'status': 'active',
            'appointment_date': fields.Date.today()
        })
        return True

    def action_revoke(self):
        """Revoke the mandate"""
        self.write({'status': 'revoked'})
        return True

    def action_extend(self):
        """Open wizard to extend the mandate"""
        self.ensure_one()
        return {
            'name': _('Extend Mandate'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.mandate.extension.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_mandate_id': self.id},
        }

    @api.model
    def get_user_mandates(self, user_id):
        """Get all active mandates for a user"""
        partner = self.env['res.users'].browse(user_id).partner_id
        return self.search([
            ('person_id', '=', partner.id),
            ('status', '=', 'active')
        ])
