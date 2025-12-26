# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfFeeWaiver(models.Model):
    _name = 'vf.fee.waiver'
    _description = 'Fee Waiver'
    _order = 'request_date desc'
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
    
    # Waiver details
    waiver_type = fields.Selection([
        ('full', 'Full Waiver'),
        ('partial', 'Partial Waiver'),
        ('discount', 'Discount'),
    ], string='Waiver Type', required=True, tracking=True)
    
    amount = fields.Float(
        string='Waiver Amount',
        required=True,
        digits='Account',
        tracking=True
    )
    percentage = fields.Float(
        string='Discount Percentage',
        tracking=True,
        help='Percentage discount (0-100)'
    )
    
    # Reason
    reason = fields.Text(
        string='Reason',
        required=True,
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Dates
    request_date = fields.Date(
        string='Request Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    decision_date = fields.Date(
        string='Decision Date',
        tracking=True
    )
    
    # Approval
    approved_by = fields.Many2one(
        'res.partner',
        string='Approved By',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    rejection_reason = fields.Text(
        string='Rejection Reason',
        tracking=True
    )
    
    # Supporting documents
    document_ids = fields.Many2many(
        'ir.attachment',
        'vf_waiver_document_rel',
        'waiver_id',
        'attachment_id',
        string='Supporting Documents'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('fee_id', 'waiver_type', 'amount')
    def _compute_display_name(self):
        for waiver in self:
            if waiver.fee_id:
                waiver.display_name = f'Waiver - {waiver.fee_id.display_name}'
            else:
                waiver.display_name = 'New Waiver'

    @api.constrains('amount')
    def _check_amount(self):
        for waiver in self:
            if waiver.amount <= 0:
                raise ValidationError(_('Waiver amount must be positive.'))

    @api.constrains('percentage')
    def _check_percentage(self):
        for waiver in self:
            if waiver.percentage and (waiver.percentage < 0 or waiver.percentage > 100):
                raise ValidationError(_('Percentage must be between 0 and 100.'))

    @api.onchange('waiver_type')
    def _onchange_waiver_type(self):
        if self.waiver_type == 'full':
            self.amount = self.fee_id.amount
            self.percentage = 100
        elif self.waiver_type == 'discount':
            if not self.percentage:
                self.percentage = 50
            if self.fee_id:
                self.amount = self.fee_id.amount * (self.percentage / 100)

    @api.onchange('percentage')
    def _onchange_percentage(self):
        if self.waiver_type == 'discount' and self.percentage and self.fee_id:
            self.amount = self.fee_id.amount * (self.percentage / 100)

    def action_request(self):
        """Submit waiver request"""
        self.write({
            'state': 'requested',
            'request_date': fields.Date.today(),
        })
        # Send notification to treasurer/admin
        template = self.env.ref('vf_membership_fees.email_template_waiver_request')
        if template:
            template.send_mail(self.id)
        return True

    def action_approve(self):
        """Approve the waiver"""
        for waiver in self:
            waiver.write({
                'state': 'approved',
                'decision_date': fields.Date.today(),
                'approved_by': self.env.user.partner_id.id,
            })
            
            # Update fee
            fee = waiver.fee_id
            fee.write({
                'waiver_id': waiver.id,
                'waived_amount': waiver.amount,
                'state': 'waived',
            })
        
        return True

    def action_reject(self):
        """Reject the waiver"""
        self.write({
            'state': 'rejected',
            'decision_date': fields.Date.today(),
        })
        return True

    def action_set_to_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True
