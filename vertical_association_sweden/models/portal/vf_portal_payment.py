# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class VfPortalPayment(models.Model):
    _name = 'vf.portal.payment'
    _description = 'Portal Payment Management'
    _inherit = ['vf.fee.payment']

    # Portal specific fields
    paid_via_portal = fields.Boolean(
        string='Paid via Portal',
        default=False
    )
    payment_method = fields.Selection([
        ('bank_transfer', 'Bank Transfer'),
        ('swish', 'Swish'),
        ('card', 'Credit Card'),
        ('invoice', 'Invoice'),
    ], string='Payment Method', required=True)
    
    # Online payment
    transaction_id = fields.Char(
        string='Transaction ID',
        readonly=True
    )
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string='Payment Status', default='pending', readonly=True)
    
    # Refund
    refund_amount = fields.Float(
        string='Refund Amount',
        digits='Account'
    )
    refund_reason = fields.Text(
        string='Refund Reason'
    )
    refund_date = fields.Date(
        string='Refund Date'
    )

    @api.model
    def create_portal_payment(self, fee_ids, payment_method, member_id):
        """Create payment via portal"""
        fees = self.env['vf.fee'].browse(fee_ids)
        
        # Validate fees belong to member
        if not all(fee.member_id.id == member_id for fee in fees):
            raise ValidationError(_('Invalid fees selected.'))
        
        # Calculate total amount
        total_amount = sum(fee.remaining_amount for fee in fees)
        
        # Create payment
        payment = self.create({
            'fee_ids': [(6, 0, fee_ids)],
            'member_id': member_id,
            'amount': total_amount,
            'payment_method': payment_method,
            'paid_via_portal': True,
            'payment_date': fields.Date.today(),
        })
        
        return payment

    def action_process_payment(self):
        """Process the payment"""
        self.ensure_one()
        
        if self.payment_status not in ['pending']:
            raise UserError(_('Payment has already been processed.'))
        
        self.write({'payment_status': 'processing'})
        
        # Process based on payment method
        if self.payment_method == 'swish':
            return self._process_swish_payment()
        elif self.payment_method == 'card':
            return self._process_card_payment()
        elif self.payment_method == 'bank_transfer':
            return self._process_bank_transfer()
        elif self.payment_method == 'invoice':
            return self._process_invoice()
        
        return True

    def _process_swish_payment(self):
        """Process Swish payment"""
        # Generate Swish payment request
        payment_request = {
            'amount': self.amount,
            'currency': self.currency_id.name,
            'message': f'Payment for fees - {self.member_id.membership_number}',
        }
        
        # In practice, integrate with Swish API
        # For now, simulate success
        self.write({
            'payment_status': 'completed',
            'transaction_id': f'SWISH-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}',
        })
        
        # Update fees
        self._update_fees_payment()
        
        return True

    def _process_card_payment(self):
        """Process credit card payment"""
        # In practice, integrate with payment gateway
        # For now, simulate success
        self.write({
            'payment_status': 'completed',
            'transaction_id': f'CARD-{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}',
        })
        
        # Update fees
        self._update_fees_payment()
        
        return True

    def _process_bank_transfer(self):
        """Process bank transfer"""
        # Create payment reference
        reference = f'VF{self.id:06d}'
        
        self.write({
            'payment_status': 'pending',
            'transaction_id': reference,
        })
        
        # Send payment instructions
        self._send_payment_instructions(reference)
        
        return True

    def _process_invoice(self):
        """Process invoice payment"""
        # Create invoice in accounting system
        invoice_vals = {
            'type': 'out_invoice',
            'partner_id': self.member_id.partner_id.id,
            'invoice_date': fields.Date.today(),
            'merchandise_order_id': self.id,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Add invoice lines for each fee
        for fee in self.fee_ids:
            invoice_line_vals = {
                'move_id': invoice.id,
                'name': fee.fee_type_id.name,
                'quantity': 1,
                'price_unit': fee.remaining_amount,
            }
            self.env['account.move.line'].create(invoice_line_vals)
        
        invoice.action_post()
        
        self.write({
            'payment_status': 'pending',
            'transaction_id': invoice.name,
        })
        
        return True

    def _update_fees_payment(self):
        """Update fee payment status"""
        if self.payment_status == 'completed':
            remaining = self.amount
            for fee in self.fee_ids:
                if remaining <= 0:
                    break
                
                to_pay = min(remaining, fee.remaining_amount)
                fee.write({'paid_amount': fee.paid_amount + to_pay})
                remaining -= to_pay
                
                if fee.remaining_amount <= 0:
                    fee.write({'state': 'paid'})

    def _send_payment_instructions(self, reference):
        """Send payment instructions to member"""
        template = self.env.ref('vertical_association_sweden.email_template_payment_instructions')
        if template:
            template.send_mail(self.id, force_send=True)

    def action_refund(self, amount, reason):
        """Process refund"""
        self.ensure_one()
        
        if self.payment_status != 'completed':
            raise UserError(_('Only completed payments can be refunded.'))
        
        if amount > self.amount:
            raise ValidationError(_('Refund amount cannot exceed payment amount.'))
        
        self.write({
            'refund_amount': amount,
            'refund_reason': reason,
            'refund_date': fields.Date.today(),
        })
        
        # Process refund based on payment method
        if self.payment_method in ['swish', 'card']:
            self._process_online_refund(amount)
        
        return True

    def _process_online_refund(self, amount):
        """Process online refund"""
        # In practice, integrate with payment provider
        # For now, just mark as refunded
        pass

    @api.model
    def get_payment_history(self, member_id):
        """Get payment history for member"""
        payments = self.search([
            ('member_id', '=', member_id),
            ('paid_via_portal', '=', True)
        ])
        
        return [{
            'id': payment.id,
            'amount': payment.amount,
            'payment_method': payment.payment_method,
            'payment_date': payment.payment_date,
            'payment_status': payment.payment_status,
            'fees': [{
                'name': fee.fee_type_id.name,
                'date_due': fee.date_due,
                'amount': fee.amount,
            } for fee in payment.fee_ids],
        } for payment in payments]
