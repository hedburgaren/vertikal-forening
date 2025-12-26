# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfMember(models.Model):
    _inherit = 'vf.member'

    # Economy-related fields
    total_fees = fields.Float(
        compute='_compute_economy_summary',
        string='Total Fees'
    )
    total_paid = fields.Float(
        compute='_compute_economy_summary',
        string='Total Paid'
    )
    total_outstanding = fields.Float(
        compute='_compute_economy_summary',
        string='Total Outstanding'
    )
    overdue_amount = fields.Float(
        compute='_compute_economy_summary',
        string='Overdue Amount'
    )
    last_payment_date = fields.Date(
        compute='_compute_last_payment_date',
        string='Last Payment Date'
    )
    payment_status = fields.Selection([
        ('up_to_date', 'Up to Date'),
        ('partial', 'Partial Payment'),
        ('overdue', 'Overdue'),
        ('no_payments', 'No Payments'),
    ], compute='_compute_payment_status', string='Payment Status')
    
    # Quick access buttons
    economy_count = fields.Integer(
        compute='_compute_economy_count',
        string='Economy Records'
    )

    @api.depends('fee_ids')
    def _compute_economy_summary(self):
        for member in self:
            fees = member.fee_ids.filtered(lambda f: f.state != 'cancelled')
            member.total_fees = sum(fees.mapped('amount'))
            member.total_paid = sum(fees.mapped('paid_amount'))
            member.total_outstanding = sum(fees.mapped('remaining_amount'))
            member.overdue_amount = sum(fees.filtered(lambda f: f.state == 'overdue').mapped('remaining_amount'))

    @api.depends('fee_ids.payment_ids')
    def _compute_last_payment_date(self):
        for member in self:
            payments = member.fee_ids.mapped('payment_ids')
            if payments:
                member.last_payment_date = max(payments.mapped('payment_date'))
            else:
                member.last_payment_date = False

    @api.depends('total_outstanding', 'overdue_amount', 'total_fees', 'total_paid')
    def _compute_payment_status(self):
        for member in self:
            if member.total_fees == 0:
                member.payment_status = 'no_payments'
            elif member.overdue_amount > 0:
                member.payment_status = 'overdue'
            elif member.total_outstanding > 0:
                member.payment_status = 'partial'
            else:
                member.payment_status = 'up_to_date'

    @api.depends('fee_ids')
    def _compute_economy_count(self):
        for member in self:
            member.economy_count = len(member.fee_ids)

    def action_view_fees(self):
        """View all fees for this member"""
        self.ensure_one()
        
        action = self.env.ref('vf_membership_fees.vf_fee_action').read()[0]
        action['domain'] = [('member_id', '=', self.id)]
        action['context'] = {'default_member_id': self.id}
        return action

    def action_view_payments(self):
        """View all payments for this member"""
        self.ensure_one()
        
        fees = self.fee_ids
        payments = fees.mapped('payment_ids')
        
        action = self.env.ref('vf_membership_fees.vf_fee_payment_action').read()[0]
        action['domain'] = [('id', 'in', payments.ids)]
        return action

    def action_send_payment_reminder(self):
        """Send payment reminder to this member"""
        self.ensure_one()
        
        if self.total_outstanding <= 0:
            raise UserError(_('This member has no outstanding payments.'))
        
        # Find outstanding fees
        outstanding_fees = self.fee_ids.filtered(
            lambda f: f.state in ['pending', 'overdue'] and f.remaining_amount > 0
        )
        
        return {
            'name': _('Send Payment Reminder'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.payment.reminder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_member_ids': [(4, self.id)],
                'default_fee_ids': [(6, 0, outstanding_fees.ids)],
            },
        }

    def action_generate_payment_statement(self):
        """Generate payment statement for this member"""
        self.ensure_one()
        
        # Create a temporary report
        report = self.env['vf.economy.report'].create({
            'name': f'Payment Statement - {self.membership_number}',
            'report_type': 'payment_status',
            'date_from': fields.Date.today().replace(month=1, day=1),
            'date_to': fields.Date.today(),
        })
        
        # Filter for this member only
        # This would require modifying the report generation to accept member filter
        
        return report.action_generate()
