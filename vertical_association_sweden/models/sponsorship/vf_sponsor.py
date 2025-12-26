# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfSponsor(models.Model):
    _name = 'vf.sponsor'
    _description = 'Association Sponsor'
    _order = 'name'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Sponsor Name',
        required=True,
        tracking=True
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    
    # Sponsorship details
    sponsorship_level_id = fields.Many2one(
        'vf.sponsorship.level',
        string='Sponsorship Level',
        required=True,
        tracking=True
    )
    
    # Dates
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True
    )
    
    # Financial
    annual_amount = fields.Float(
        string='Annual Amount',
        required=True,
        tracking=True,
        digits='Account'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Payment Terms'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Branding
    logo = fields.Binary(
        string='Logo',
        tracking=True
    )
    website_url = fields.Char(
        string='Website',
        tracking=True
    )
    description = fields.Text(
        string='Description',
        tracking=True
    )
    
    # Contacts
    contact_ids = fields.One2many(
        'res.partner',
        'sponsor_id',
        string='Contact Persons',
        domain=[('is_company', '=', False)]
    )
    primary_contact_id = fields.Many2one(
        'res.partner',
        string='Primary Contact',
        domain=[('is_company', '=', False)]
    )
    
    # Benefits and agreements
    contract_ids = fields.One2many(
        'vf.sponsorship.contract',
        'sponsor_id',
        string='Contracts'
    )
    benefit_ids = fields.Many2many(
        'vf.sponsorship.benefit',
        string='Custom Benefits'
    )
    
    # Visibility
    show_on_website = fields.Boolean(
        string='Show on Website',
        default=True,
        tracking=True
    )
    featured_sponsor = fields.Boolean(
        string='Featured Sponsor',
        default=False,
        tracking=True
    )
    
    # Computed fields
    is_active = fields.Boolean(
        compute='_compute_is_active',
        store=True
    )
    days_remaining = fields.Integer(
        compute='_compute_days_remaining',
        string='Days Remaining'
    )

    @api.depends('state', 'start_date', 'end_date')
    def _compute_is_active(self):
        today = fields.Date.today()
        for sponsor in self:
            sponsor.is_active = (
                sponsor.state == 'active' and
                sponsor.start_date <= today <= sponsor.end_date
            )

    @api.depends('end_date', 'state')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for sponsor in self:
            if sponsor.state == 'active' and sponsor.end_date:
                sponsor.days_remaining = (sponsor.end_date - today).days
            else:
                sponsor.days_remaining = 0

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for sponsor in self:
            if sponsor.start_date >= sponsor.end_date:
                raise ValidationError(_('End date must be after start date.'))

    @api.constrains('partner_id')
    def _check_unique_partner(self):
        for sponsor in self:
            existing = self.search([
                ('partner_id', '=', sponsor.partner_id.id),
                ('state', 'in', ['draft', 'active']),
                ('id', '!=', sponsor.id)
            ])
            if existing:
                raise ValidationError(_('A sponsor with this partner already exists.'))

    def action_activate(self):
        """Activate the sponsorship"""
        self.write({'state': 'active'})
        return True

    def action_terminate(self):
        """Terminate the sponsorship"""
        self.write({'state': 'terminated'})
        return True

    def action_renew(self):
        """Renew the sponsorship"""
        self.ensure_one()
        return {
            'name': _('Renew Sponsorship'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.sponsor.renewal.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sponsor_id': self.id},
        }

    def action_view_contracts(self):
        """View all contracts"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_sponsorship_contract_action').read()[0]
        action['domain'] = [('sponsor_id', '=', self.id)]
        return action

    def action_create_contract(self):
        """Create a new contract"""
        self.ensure_one()
        return {
            'name': _('Create Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.sponsorship.contract',
            'view_mode': 'form',
            'target': 'current',
            'context': {'default_sponsor_id': self.id},
        }

    @api.model
    def get_expiring_sponsors(self, days=30):
        """Get sponsors expiring within X days"""
        cutoff_date = fields.Date.today() + timedelta(days=days)
        return self.search([
            ('state', '=', 'active'),
            ('end_date', '<=', cutoff_date),
            ('end_date', '>=', fields.Date.today()),
        ])

    @api.model
    def process_expired_sponsors(self):
        """Process expired sponsorships"""
        expired = self.search([
            ('state', '=', 'active'),
            ('end_date', '<', fields.Date.today()),
        ])
        expired.write({'state': 'expired'})
        return len(expired)
