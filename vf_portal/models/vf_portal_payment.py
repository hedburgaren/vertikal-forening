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
    def create_portal_payment(self, fee_id, payment_method, amount=None):
        """Create payment via portal"""
        fee = self.env['vf.fee'].browse(fee_id)
        
        if fee.state == 'paid':
            raise UserError(_('This fee has already been paid.'))
        
        if amount is None:
            amount = fee.remaining_amount
        
        if amount <= 0:
            raise UserError(_('Payment amount must be greater than zero.'))
        
        if amount > fee.remaining_amount:
            raise UserError(_('Payment amount cannot exceed remaining amount.'))
        
        # Create payment record
        payment = self.create({
            'fee_id': fee_id,
            'amount': amount,
            'payment_method': payment_method,
            'paid_via_portal': True,
            'payment_date': fields.Date.today(),
        })
        
        # Process payment based on method
        if payment_method in ['swish', 'card']:
            payment._process_online_payment()
        elif payment_method == 'bank_transfer':
            payment._process_bank_transfer()
        elif payment_method == 'invoice':
            payment._process_invoice()
        
        return payment

    def _process_online_payment(self):
        """Process online payment (Swish/Card)"""
        self.ensure_one()
        
        # Generate transaction ID
        self.transaction_id = f'TX{fields.Datetime.now().strftime("%Y%m%d%H%M%S")}{self.id}'
        self.payment_status = 'processing'
        
        # In real implementation, integrate with payment provider
        # For now, simulate successful payment
        self._complete_payment()

    def _process_bank_transfer(self):
        """Process bank transfer"""
        self.ensure_one()
        
        self.payment_status = 'pending'
        
        # Send payment instructions
        template = self.env.ref('vf_portal.email_template_bank_transfer_instructions')
        template.send_mail(self.id)

    def _process_invoice(self):
        """Process invoice payment"""
        self.ensure_one()
        
        # Create invoice in accounting
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': self.fee_id.member_id.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': self.fee_id.name,
                'quantity': 1,
                'price_unit': self.amount,
            })],
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        invoice.action_post()
        
        # Send invoice
        template = self.env.ref('vf_portal.email_template_invoice')
        template.send_mail(
            self.id,
            email_values={
                'attachment_ids': [(4, invoice.id)],
            }
        )
        
        self.payment_status = 'pending'

    def _complete_payment(self):
        """Mark payment as completed"""
        self.ensure_one()
        
        self.payment_status = 'completed'
        self.state = 'confirmed'
        
        # Update fee
        fee = self.fee_id
        fee._compute_paid_amount()
        
        # Send confirmation
        template = self.env.ref('vf_portal.email_template_payment_confirmation')
        template.send_mail(self.id)

    def action_refund(self, amount, reason):
        """Process refund"""
        self.ensure_one()
        
        if self.payment_status != 'completed':
            raise UserError(_('Can only refund completed payments.'))
        
        if amount > self.amount:
            raise UserError(_('Refund amount cannot exceed payment amount.'))
        
        # Create refund record
        self.write({
            'refund_amount': amount,
            'refund_reason': reason,
            'refund_date': fields.Date.today(),
        })
        
        # Process refund (integration with payment provider)
        # For now, just mark as refunded
        self.payment_status = 'cancelled'
        
        # Update fee
        fee = self.fee_id
        fee._compute_paid_amount()
        
        return True

    def action_view_payment_details(self):
        """View payment details"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Details',
            'res_model': 'vf.portal.payment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'form_view_initial_mode': 'readonly',
            },
        }


class VfPortalPaymentPlan(models.Model):
    _name = 'vf.portal.payment.plan'
    _description = 'Portal Payment Plan'
    _order = 'start_date'

    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        ondelete='cascade'
    )
    fee_ids = fields.Many2many(
        'vf.fee',
        string='Fees',
        required=True
    )
    
    # Plan details
    name = fields.Char(
        string='Plan Name',
        required=True
    )
    total_amount = fields.Float(
        compute='_compute_totals',
        string='Total Amount',
        digits='Account',
        store=True
    )
    paid_amount = fields.Float(
        compute='_compute_totals',
        string='Paid Amount',
        digits='Account',
        store=True
    )
    remaining_amount = fields.Float(
        compute='_compute_totals',
        string='Remaining Amount',
        digits='Account',
        store=True
    )
    
    # Schedule
    payment_count = fields.Integer(
        string='Number of Payments',
        required=True,
        default=1
    )
    payment_amount = fields.Float(
        string='Payment Amount',
        required=True,
        digits='Account'
    )
    payment_frequency = fields.Selection([
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ], string='Payment Frequency', default='monthly')
    
    # Dates
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.today
    )
    end_date = fields.Date(
        compute='_compute_end_date',
        string='End Date',
        store=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True)
    
    # Payments
    payment_ids = fields.One2many(
        'vf.portal.payment.plan.line',
        'plan_id',
        string='Scheduled Payments'
    )

    @api.depends('fee_ids')
    def _compute_totals(self):
        for plan in self:
            plan.total_amount = sum(plan.fee_ids.mapped('amount'))
            plan.paid_amount = sum(plan.fee_ids.mapped('paid_amount'))
            plan.remaining_amount = plan.total_amount - plan.paid_amount

    @api.depends('start_date', 'payment_count', 'payment_frequency')
    def _compute_end_date(self):
        for plan in self:
            if plan.start_date and plan.payment_count > 0:
                if plan.payment_frequency == 'weekly':
                    delta = datetime.timedelta(weeks=plan.payment_count - 1)
                elif plan.payment_frequency == 'biweekly':
                    delta = datetime.timedelta(weeks=2 * (plan.payment_count - 1))
                else:  # monthly
                    delta = datetime.timedelta(days=30 * (plan.payment_count - 1))
                
                plan.end_date = plan.start_date + delta

    def action_activate(self):
        """Activate payment plan"""
        self.ensure_one()
        
        # Create scheduled payments
        self._generate_payment_schedule()
        
        self.state = 'active'
        return True

    def _generate_payment_schedule(self):
        """Generate payment schedule"""
        self.payment_ids.unlink()
        
        for i in range(self.payment_count):
            if self.payment_frequency == 'weekly':
                date = fields.Date.add(self.start_date, weeks=i)
            elif self.payment_frequency == 'biweekly':
                date = fields.Date.add(self.start_date, weeks=2*i)
            else:  # monthly
                date = fields.Date.add(self.start_date, months=i)
            
            self.env['vf.portal.payment.plan.line'].create({
                'plan_id': self.id,
                'payment_number': i + 1,
                'due_date': date,
                'amount': self.payment_amount,
            })


class VfPortalPaymentPlanLine(models.Model):
    _name = 'vf.portal.payment.plan.line'
    _description = 'Portal Payment Plan Line'
    _order = 'payment_number'

    plan_id = fields.Many2one(
        'vf.portal.payment.plan',
        string='Payment Plan',
        required=True,
        ondelete='cascade'
    )
    payment_number = fields.Integer(
        string='Payment Number',
        required=True
    )
    due_date = fields.Date(
        string='Due Date',
        required=True
    )
    amount = fields.Float(
        string='Amount',
        required=True,
        digits='Account'
    )
    paid = fields.Boolean(
        string='Paid',
        default=False
    )
    paid_date = fields.Date(
        string='Paid Date'
    )
    payment_id = fields.Many2one(
        'vf.portal.payment',
        string='Payment'
    )
