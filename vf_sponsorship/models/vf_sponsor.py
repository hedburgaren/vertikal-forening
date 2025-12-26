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
    
    # Status
    state = fields.Selection([
        ('prospect', 'Prospect'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Status', default='prospect', required=True, tracking=True)
    
    # Benefits and visibility
    logo_id = fields.Many2one(
        'ir.attachment',
        string='Logo',
        domain="[('res_field', '=', False), ('res_model', '=', False)]"
    )
    website_url = fields.Char(
        string='Website URL'
    )
    description = fields.Html(
        string='Description'
    )
    
    # Benefits provided
    benefit_ids = fields.Many2many(
        'vf.sponsorship.benefit',
        string='Benefits'
    )
    
    # Contracts
    contract_ids = fields.One2many(
        'vf.sponsorship.contract',
        'sponsor_id',
        string='Contracts'
    )
    
    # Communication preferences
    contact_person_id = fields.Many2one(
        'res.partner',
        string='Contact Person',
        tracking=True
    )
    communication_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannually', 'Biannually'),
        ('annually', 'Annually'),
    ], string='Communication Frequency', default='quarterly')
    
    # Statistics
    total_invoiced = fields.Float(
        compute='_compute_statistics',
        string='Total Invoiced',
        digits='Account'
    )
    total_paid = fields.Float(
        compute='_compute_statistics',
        string='Total Paid',
        digits='Account'
    )
    outstanding_amount = fields.Float(
        compute='_compute_statistics',
        string='Outstanding Amount',
        digits='Account'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    _sql_constraints = [
        ('date_check', 'CHECK(start_date <= end_date)', 
         'Start date must be before or equal to end date!'),
        ('unique_partner_active', 'UNIQUE(partner_id, state) WHERE state IN (\'active\', \'prospect\')', 
         'Partner can only have one active or prospect sponsorship!'),
    ]

    @api.depends('partner_id', 'sponsorship_level_id')
    def _compute_display_name(self):
        for sponsor in self:
            if sponsor.partner_id and sponsor.sponsorship_level_id:
                sponsor.display_name = f'{sponsor.partner_id.name} - {sponsor.sponsorship_level_id.name}'
            elif sponsor.partner_id:
                sponsor.display_name = sponsor.partner_id.name
            else:
                sponsor.display_name = 'New Sponsor'

    @api.depends('contract_ids')
    def _compute_statistics(self):
        for sponsor in self:
            contracts = sponsor.contract_ids.filtered(lambda c: c.state != 'cancelled')
            sponsor.total_invoiced = sum(contracts.mapped('total_amount'))
            sponsor.total_paid = sum(contracts.mapped('paid_amount'))
            sponsor.outstanding_amount = sum(contracts.mapped('remaining_amount'))

    @api.onchange('sponsorship_level_id')
    def _onchange_sponsorship_level(self):
        """Update benefits based on sponsorship level"""
        if self.sponsorship_level_id:
            self.annual_amount = self.sponsorship_level_id.default_amount
            self.benefit_ids = self.sponsorship_level_id.benefit_ids

    def action_activate(self):
        """Activate the sponsorship"""
        self.ensure_one()
        if self.state == 'prospect':
            self.state = 'active'
            # Create initial contract
            self._create_initial_contract()
        return True

    def action_terminate(self):
        """Terminate the sponsorship"""
        self.ensure_one()
        self.state = 'terminated'
        # Cancel all active contracts
        self.contract_ids.filtered(lambda c: c.state == 'active').write({'state': 'cancelled'})
        return True

    def action_renew(self):
        """Renew the sponsorship"""
        self.ensure_one()
        
        # Create renewal contract
        self._create_renewal_contract()
        
        # Update dates
        self.end_date = fields.Date.add(self.end_date, years=1)
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renewal Contract',
            'res_model': 'vf.sponsorship.contract',
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_initial_contract(self):
        """Create initial sponsorship contract"""
        self.env['vf.sponsorship.contract'].create({
            'sponsor_id': self.id,
            'type': 'initial',
            'start_date': self.start_date,
            'end_date': self.end_date,
            'amount': self.annual_amount,
            'currency_id': self.currency_id.id,
        })

    def _create_renewal_contract(self):
        """Create renewal sponsorship contract"""
        self.env['vf.sponsorship.contract'].create({
            'sponsor_id': self.id,
            'type': 'renewal',
            'start_date': self.end_date + datetime.timedelta(days=1),
            'end_date': fields.Date.add(self.end_date, years=1),
            'amount': self.annual_amount,
            'currency_id': self.currency_id.id,
        })

    def action_view_contracts(self):
        """View all contracts for this sponsor"""
        self.ensure_one()
        
        action = self.env.ref('vf_sponsorship.vf_sponsorship_contract_action').read()[0]
        action['domain'] = [('sponsor_id', '=', self.id)]
        action['context'] = {'default_sponsor_id': self.id}
        return action

    def action_send_update(self):
        """Send sponsor update report"""
        self.ensure_one()
        
        # Create sponsor report
        report = self.env['vf.sponsor.report'].create({
            'sponsor_id': self.id,
            'report_type': 'sponsor_update',
        })
        
        # Generate and send
        attachment = report._generate_report()
        
        template = self.env.ref('vf_sponsorship.email_template_sponsor_update')
        template.send_mail(
            self.id,
            email_values={
                'email_to': self.contact_person_id.email or self.partner_id.email,
                'attachment_ids': [(4, attachment.id)],
            }
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Update Sent'),
                'message': _('Sponsor update has been sent to %s') % (self.contact_person_id.name or self.partner_id.name),
                'type': 'success',
            }
        }

    @api.model
    def check_expiring_sponsors(self):
        """Cron job to check for expiring sponsorships"""
        thirty_days = fields.Date.today() + datetime.timedelta(days=30)
        expiring = self.search([
            ('state', '=', 'active'),
            ('end_date', '=', thirty_days)
        ])
        
        for sponsor in expiring:
            # Send renewal reminder
            template = self.env.ref('vf_sponsorship.email_template_renewal_reminder')
            template.send_mail(
                sponsor.id,
                email_values={
                    'email_to': sponsor.contact_person_id.email or sponsor.partner_id.email,
                }
            )
            
            # Create activity
            sponsor.activity_schedule(
                'vf_sponsorship.mail_activity_sponsor_renewal',
                user_id=self.env.ref('base.user_admin').id,
                note=_('Sponsorship expires in 30 days')
            )
