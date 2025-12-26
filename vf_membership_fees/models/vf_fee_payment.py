# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfFeePayment(models.Model):
    _name = 'vf.fee.payment'
    _description = 'Fee Payment'
    _order = 'payment_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    fee_id = fields.Many2one(
        'vf.fee',
        string='Fee',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    member_id = fields.Many2one(
        'vf.member',
        related='fee_id.member_id',
        store=True,
        readonly=True
    )
    
    # Payment details
    amount = fields.Float(
        string='Amount',
        required=True,
        digits='Account',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='fee_id.currency_id',
        store=True,
        readonly=True
    )
    
    # Payment method
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card'),
        ('online', 'Online Payment'),
        ('direct_debit', 'Direct Debit'),
        ('other', 'Other'),
    ], string='Payment Method', required=True, tracking=True)
    
    # Reference
    reference = fields.Char(
        string='Reference',
        tracking=True,
        help='Transaction reference or receipt number'
    )
    
    # Dates
    payment_date = fields.Date(
        string='Payment Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Notes
    notes = fields.Text(
        string='Notes',
        tracking=True
    )
    
    # Recorded by
    recorded_by = fields.Many2one(
        'res.partner',
        string='Recorded By',
        default=lambda self: self.env.user.partner_id,
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Accounting link (optional)
    move_line_id = fields.Many2one(
        'account.move.line',
        string='Journal Item',
        readonly=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('fee_id', 'payment_date', 'amount')
    def _compute_display_name(self):
        for payment in self:
            if payment.fee_id and payment.payment_date:
                date_str = payment.payment_date.strftime('%Y-%m-%d')
                payment.display_name = f'Payment {date_str} - {payment.amount} {payment.currency_id.symbol}'
            else:
                payment.display_name = 'New Payment'

    @api.constrains('amount')
    def _check_amount(self):
        for payment in self:
            if payment.amount <= 0:
                raise ValidationError(_('Amount must be positive.'))

    @api.constrains('fee_id', 'amount')
    def _check_overpayment(self):
        for payment in self:
            if payment.fee_id and payment.state == 'confirmed':
                total_paid = payment.fee_id.paid_amount + payment.amount
                if total_paid > payment.fee_id.amount:
                    raise ValidationError(_('Payment amount exceeds the fee amount.'))

    def action_confirm(self):
        """Confirm the payment"""
        for payment in self:
            payment.write({'state': 'confirmed'})
            
            # Update fee status if fully paid
            fee = payment.fee_id
            if fee.remaining_amount <= 0:
                fee.action_mark_paid()
            elif fee.state == 'draft':
                fee.action_confirm()
        
        return True

    def action_cancel(self):
        """Cancel the payment"""
        self.write({'state': 'cancelled'})
        return True

    def action_set_to_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True

    @api.model
    def create_payment(self, fee_id, amount, payment_method, **kwargs):
        """Helper method to create a payment"""
        fee = self.env['vf.fee'].browse(fee_id)
        
        if not fee.exists():
            raise ValidationError(_('Fee not found.'))
        
        if amount > fee.remaining_amount:
            raise ValidationError(_('Payment amount exceeds remaining amount.'))
        
        payment_vals = {
            'fee_id': fee_id,
            'amount': amount,
            'payment_method': payment_method,
            'state': 'confirmed',
        }
        payment_vals.update(kwargs)
        
        return self.create(payment_vals)
