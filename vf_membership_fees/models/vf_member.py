# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfMember(models.Model):
    _inherit = 'vf.member'

    # Fee relationships
    fee_ids = fields.One2many(
        'vf.fee',
        'member_id',
        string='Fees'
    )
    waiver_ids = fields.One2many(
        'vf.fee.waiver',
        'member_id',
        string='Waivers'
    )
    
    # Fee settings
    fee_category_id = fields.Many2one(
        'vf.fee.category',
        string='Fee Category',
        tracking=True,
        help='Default fee category for this member'
    )
    
    # Payment preferences
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
        ('direct_debit', 'Direct Debit'),
        ('online', 'Online Payment'),
    ], string='Preferred Payment Method', tracking=True)
    
    # Statistics
    total_fees = fields.Float(
        compute='_compute_fee_statistics',
        string='Total Fees',
        digits='Account'
    )
    total_paid = fields.Float(
        compute='_compute_fee_statistics',
        string='Total Paid',
        digits='Account'
    )
    total_outstanding = fields.Float(
        compute='_compute_fee_statistics',
        string='Total Outstanding',
        digits='Account'
    )
    overdue_fees = fields.Integer(
        compute='_compute_fee_statistics',
        string='Overdue Fees'
    )
    
    # Computed fields
    has_overdue_fees = fields.Boolean(
        compute='_compute_has_overdue',
        string='Has Overdue Fees'
    )

    def _compute_fee_statistics(self):
        """Compute fee statistics for member"""
        for member in self:
            fees = member.fee_ids.filtered(lambda f: f.state != 'cancelled')
            member.total_fees = sum(fees.mapped('amount'))
            member.total_paid = sum(fees.mapped('paid_amount'))
            member.total_outstanding = sum(fees.mapped('remaining_amount'))
            member.overdue_fees = len(fees.filtered(lambda f: f.is_overdue))

    def _compute_has_overdue(self):
        """Check if member has overdue fees"""
        for member in self:
            member.has_overdue_fees = member.overdue_fees > 0

    def action_view_fees(self):
        """View member's fees"""
        self.ensure_one()
        return {
            'name': _('Membership Fees'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.fee',
            'view_mode': 'tree,form',
            'domain': [('member_id', '=', self.id)],
            'context': {'default_member_id': self.id},
        }

    def action_make_payment(self):
        """Open payment wizard"""
        self.ensure_one()
        return {
            'name': _('Make Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.fee.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_member_id': self.id,
                'default_fee_ids': self.fee_ids.filtered(
                    lambda f: f.state in ['pending', 'overdue']
                ).ids,
            },
        }

    def action_request_waiver(self):
        """Open waiver request wizard"""
        self.ensure_one()
        return {
            'name': _('Request Waiver'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.fee.waiver.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_member_id': self.id,
                'default_fee_ids': self.fee_ids.filtered(
                    lambda f: f.state in ['pending', 'overdue']
                ).ids,
            },
        }

    def generate_fees(self, category_ids=None):
        """Generate fees for this member"""
        self.ensure_one()
        return self.env['vf.fee'].generate_fees(
            category_ids=category_ids,
            date=fields.Date.today()
        )

    def get_next_fee_due(self):
        """Get next fee due date and amount"""
        pending_fees = self.fee_ids.filtered(
            lambda f: f.state in ['pending', 'overdue']
        ).sorted('due_date')
        
        if pending_fees:
            return {
                'due_date': pending_fees[0].due_date,
                'amount': pending_fees[0].remaining_amount,
                'fee_id': pending_fees[0].id,
            }
        return None
