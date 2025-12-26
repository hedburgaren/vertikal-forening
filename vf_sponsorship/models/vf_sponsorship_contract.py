# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfSponsorshipContract(models.Model):
    _name = 'vf.sponsorship.contract'
    _description = 'Sponsorship Contract'
    _order = 'start_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    sponsor_id = fields.Many2one(
        'vf.sponsor',
        string='Sponsor',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Contract details
    contract_number = fields.Char(
        string='Contract Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    type = fields.Selection([
        ('initial', 'Initial'),
        ('renewal', 'Renewal'),
        ('amendment', 'Amendment'),
    ], string='Contract Type', required=True, default='initial')
    
    # Dates
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
    signed_date = fields.Date(
        string='Signed Date',
        tracking=True
    )
    
    # Financial
    amount = fields.Float(
        string='Contract Amount',
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
    
    # Payment terms
    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Payment Terms'
    )
    payment_schedule = fields.Selection([
        ('annual', 'Annual'),
        ('semiannual', 'Semi-Annual'),
        ('quarterly', 'Quarterly'),
        ('monthly', 'Monthly'),
    ], string='Payment Schedule', default='annual')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent for Signature'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Documents
    contract_document_id = fields.Many2one(
        'ir.attachment',
        string='Contract Document'
    )
    signed_document_id = fields.Many2one(
        'ir.attachment',
        string='Signed Document'
    )
    
    # Invoice tracking
    invoice_ids = fields.One2many(
        'account.move',
        'sponsorship_contract_id',
        string='Invoices'
    )
    total_amount = fields.Float(
        compute='_compute_invoice_totals',
        string='Total Invoiced',
        digits='Account'
    )
    paid_amount = fields.Float(
        compute='_compute_invoice_totals',
        string='Total Paid',
        digits='Account'
    )
    remaining_amount = fields.Float(
        compute='_compute_invoice_totals',
        string='Remaining Amount',
        digits='Account'
    )
    
    # Notes
    notes = fields.Text(
        string='Notes'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    _sql_constraints = [
        ('contract_number_unique', 'unique(contract_number)', 
         'Contract number must be unique!'),
        ('date_check', 'CHECK(start_date <= end_date)', 
         'Start date must be before or equal to end date!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('contract_number', _('New')) == _('New'):
                vals['contract_number'] = self._generate_contract_number()
        return super().create(vals_list)

    def _generate_contract_number(self):
        """Generate unique contract number"""
        sequence = self.env['ir.sequence'].next_by_code('vf.sponsorship.contract') or '00001'
        return f'SP-{sequence}'

    @api.depends('sponsor_id', 'contract_number')
    def _compute_display_name(self):
        for contract in self:
            if contract.sponsor_id and contract.contract_number:
                contract.display_name = f'{contract.contract_number} - {contract.sponsor_id.partner_id.name}'
            else:
                contract.display_name = contract.contract_number or 'New Contract'

    @api.depends('invoice_ids.amount_total', 'invoice_ids.amount_residual')
    def _compute_invoice_totals(self):
        for contract in self:
            invoices = contract.invoice_ids.filtered(lambda i: i.state != 'cancel')
            contract.total_amount = sum(invoices.mapped('amount_total'))
            contract.paid_amount = sum(invoices.mapped('amount_paid'))
            contract.remaining_amount = sum(invoices.mapped('amount_residual'))

    def action_send_for_signature(self):
        """Send contract for signature"""
        self.ensure_one()
        if not self.contract_document_id:
            raise ValidationError(_('Please attach the contract document first.'))
        
        self.state = 'sent'
        
        # Send email
        template = self.env.ref('vf_sponsorship.email_template_contract_signature')
        template.send_mail(
            self.id,
            email_values={
                'email_to': self.sponsor_id.contact_person_id.email or self.sponsor_id.partner_id.email,
                'attachment_ids': [(4, self.contract_document_id.id)],
            }
        )
        
        return True

    def action_mark_signed(self):
        """Mark contract as signed"""
        self.ensure_one()
        if not self.signed_document_id:
            raise ValidationError(_('Please upload the signed contract document first.'))
        
        self.state = 'signed'
        self.signed_date = fields.Date.today()
        
        # Activate if start date is today or in the past
        if self.start_date <= fields.Date.today():
            self.state = 'active'
            self.sponsor_id.state = 'active'
        
        # Create first invoice
        self._create_invoice()
        
        return True

    def action_activate(self):
        """Activate the contract"""
        self.ensure_one()
        if self.state != 'signed':
            raise ValidationError(_('Contract must be signed before activation.'))
        
        self.state = 'active'
        self.sponsor_id.state = 'active'
        return True

    def action_cancel(self):
        """Cancel the contract"""
        self.ensure_one()
        self.state = 'cancelled'
        
        # Cancel unpaid invoices
        unpaid_invoices = self.invoice_ids.filtered(lambda i: i.state == 'draft')
        unpaid_invoices.button_cancel()
        
        return True

    def _create_invoice(self):
        """Create invoice for this contract"""
        if self.payment_schedule == 'annual':
            self._create_single_invoice(self.start_date, self.amount)
        elif self.payment_schedule == 'semiannual':
            amount = self.amount / 2
            self._create_single_invoice(self.start_date, amount)
            date = fields.Date.add(self.start_date, months=6)
            self._create_single_invoice(date, amount)
        elif self.payment_schedule == 'quarterly':
            amount = self.amount / 4
            for i in range(4):
                date = fields.Date.add(self.start_date, months=i*3)
                self._create_single_invoice(date, amount)
        elif self.payment_schedule == 'monthly':
            amount = self.amount / 12
            for i in range(12):
                date = fields.Date.add(self.start_date, months=i)
                self._create_single_invoice(date, amount)

    def _create_single_invoice(self, date, amount):
        """Create a single invoice"""
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.sponsor_id.partner_id.id,
            'invoice_date': date,
            'date': date,
            'payment_term_id': self.payment_term_id.id if self.payment_term_id else False,
            'sponsorship_contract_id': self.id,
            'invoice_line_ids': [(0, 0, {
                'name': f'Sponsorship {self.contract_number} - {date.strftime("%Y-%m")}',
                'quantity': 1,
                'price_unit': amount,
            })],
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()

    def action_view_invoices(self):
        """View all invoices for this contract"""
        self.ensure_one()
        
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        action['domain'] = [('sponsorship_contract_id', '=', self.id)]
        action['context'] = {'default_sponsorship_contract_id': self.id}
        return action

    def action_create_invoice(self):
        """Create additional invoice (e.g., for amendments)"""
        self.ensure_one()
        
        return {
            'name': _('Create Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_move_type': 'out_invoice',
                'default_partner_id': self.sponsor_id.partner_id.id,
                'default_sponsorship_contract_id': self.id,
            },
        }

    @api.model
    def check_expired_contracts(self):
        """Cron job to check for expired contracts"""
        today = fields.Date.today()
        expired = self.search([
            ('state', '=', 'active'),
            ('end_date', '<', today)
        ])
        
        for contract in expired:
            contract.state = 'expired'
            # Check if sponsor has other active contracts
            active_contracts = self.search_count([
                ('sponsor_id', '=', contract.sponsor_id.id),
                ('state', '=', 'active')
            ])
            if not active_contracts:
                contract.sponsor_id.state = 'expired'
