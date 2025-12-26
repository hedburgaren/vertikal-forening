# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class VfFee(models.Model):
    _name = 'vf.fee'
    _description = 'Membership Fee'
    _order = 'due_date desc, name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Description',
        required=True,
        tracking=True
    )
    category_id = fields.Many2one(
        'vf.fee.category',
        string='Fee Category',
        required=True,
        tracking=True
    )
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Financial details
    amount = fields.Float(
        string='Amount',
        required=True,
        digits='Account',
        tracking=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    # Period
    period_start = fields.Date(
        string='Period Start',
        required=True,
        tracking=True
    )
    period_end = fields.Date(
        string='Period End',
        required=True,
        tracking=True
    )
    
    # Dates
    generate_date = fields.Date(
        string='Generate Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
        ('waived', 'Waived'),
    ], string='State', default='draft', required=True, tracking=True)
    
    # Payment tracking
    paid_amount = fields.Float(
        compute='_compute_paid_amount',
        string='Paid Amount',
        digits='Account',
        store=True
    )
    remaining_amount = fields.Float(
        compute='_compute_remaining_amount',
        string='Remaining Amount',
        digits='Account',
        store=True
    )
    
    # Waiver
    waiver_id = fields.Many2one(
        'vf.fee.waiver',
        string='Waiver',
        tracking=True
    )
    waived_amount = fields.Float(
        string='Waived Amount',
        digits='Account',
        tracking=True
    )
    
    # Accounting link (optional)
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    is_overdue = fields.Boolean(
        compute='_compute_is_overdue',
        string='Is Overdue'
    )
    days_overdue = fields.Integer(
        compute='_compute_days_overdue',
        string='Days Overdue'
    )
    
    # Relationships
    payment_ids = fields.One2many(
        'vf.fee.payment',
        'fee_id',
        string='Payments'
    )

    @api.depends('name', 'member_id', 'period_start')
    def _compute_display_name(self):
        for fee in self:
            if fee.member_id and fee.period_start:
                period_str = fee.period_start.strftime('%Y-%m')
                fee.display_name = f'{fee.member_id.name} - {fee.name} ({period_str})'
            else:
                fee.display_name = fee.name

    @api.depends('payment_ids.amount', 'payment_ids.state')
    def _compute_paid_amount(self):
        for fee in self:
            fee.paid_amount = sum(
                fee.payment_ids.filtered(lambda p: p.state == 'confirmed').mapped('amount')
            )

    @api.depends('amount', 'paid_amount', 'waived_amount')
    def _compute_remaining_amount(self):
        for fee in self:
            fee.remaining_amount = fee.amount - fee.paid_amount - fee.waived_amount

    @api.depends('due_date', 'state')
    def _compute_is_overdue(self):
        for fee in self:
            fee.is_overdue = (
                fee.state in ['pending', 'overdue'] and 
                fields.Date.today() > fee.due_date
            )

    @api.depends('due_date', 'state')
    def _compute_days_overdue(self):
        for fee in self:
            if fee.is_overdue:
                fee.days_overdue = (fields.Date.today() - fee.due_date).days
            else:
                fee.days_overdue = 0

    @api.constrains('period_start', 'period_end')
    def _check_period(self):
        for fee in self:
            if fee.period_start >= fee.period_end:
                raise ValidationError(_('Period end must be after period start.'))

    @api.constrains('amount')
    def _check_amount(self):
        for fee in self:
            if fee.amount <= 0:
                raise ValidationError(_('Amount must be positive.'))

    @api.onchange('category_id')
    def _onchange_category(self):
        if self.category_id:
            self.amount = self.category_id.amount
            self.currency_id = self.category_id.currency_id

    def action_confirm(self):
        """Confirm the fee"""
        self.write({'state': 'pending'})
        # Send notification to member
        template = self.env.ref('vf_membership_fees.email_template_fee_due')
        if template:
            template.send_mail(self.id)
        return True

    def action_mark_paid(self):
        """Mark fee as fully paid"""
        self.write({'state': 'paid'})
        return True

    def action_mark_overdue(self):
        """Mark fee as overdue"""
        fees = self.filtered(lambda f: f.state == 'pending' and f.is_overdue)
        fees.write({'state': 'overdue'})
        return True

    def action_cancel(self):
        """Cancel the fee"""
        self.write({'state': 'cancelled'})
        return True

    def action_set_to_draft(self):
        """Reset to draft"""
        self.write({'state': 'draft'})
        return True

    def action_waive(self):
        """Open waiver wizard"""
        self.ensure_one()
        return {
            'name': _('Waive Fee'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.fee.waiver.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_fee_id': self.id},
        }

    def action_view_payments(self):
        """View fee payments"""
        self.ensure_one()
        return {
            'name': _('Payments'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.fee.payment',
            'view_mode': 'tree,form',
            'domain': [('fee_id', '=', self.id)],
            'context': {'default_fee_id': self.id},
        }

    def action_send_reminder(self):
        """Send payment reminder"""
        self.ensure_one()
        if self.state in ['pending', 'overdue']:
            template = self.env.ref('vf_membership_fees.email_template_fee_reminder')
            if template:
                template.send_mail(self.id)
                self.message_post(
                    body=_('Payment reminder sent to member.'),
                    message_type='notification'
                )
        return True

    @api.model
    def generate_fees(self, category_ids=None, date=None):
        """Generate fees for eligible members"""
        if not date:
            date = fields.Date.today()
        
        categories = category_ids or self.env['vf.fee.category'].search([
            ('auto_generate', '=', True),
            ('active', '=', True)
        ])
        
        for category in categories:
            # Check if it's the right day to generate
            if date.day != category.generate_day:
                continue
            
            # Get eligible members
            members = self.env['vf.member'].search([
                ('state', '=', 'active')
            ])
            
            for member in members:
                # Check if category applies to member
                applicable = self.env['vf.fee.category'].get_applicable_categories(member)
                if category not in applicable:
                    continue
                
                # Check if fee already exists for this period
                period_start = date
                period_end = self._get_period_end(date, category.period_type)
                
                existing = self.search([
                    ('member_id', '=', member.id),
                    ('category_id', '=', category.id),
                    ('period_start', '=', period_start),
                    ('period_end', '=', period_end),
                    ('state', '!=', 'cancelled')
                ])
                
                if existing:
                    continue
                
                # Create fee
                due_date = date + timedelta(days=category.due_days)
                self.create({
                    'name': category.name,
                    'category_id': category.id,
                    'member_id': member.id,
                    'amount': category.amount,
                    'currency_id': category.currency_id.id,
                    'period_start': period_start,
                    'period_end': period_end,
                    'generate_date': date,
                    'due_date': due_date,
                    'state': 'pending',
                })
        
        return True

    def _get_period_end(self, start_date, period_type):
        """Calculate period end date based on period type"""
        if period_type == 'monthly':
            # End of month
            if start_date.month == 12:
                return start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                return start_date.replace(month=start_date.month + 1, day=1) - timedelta(days=1)
        
        elif period_type == 'quarterly':
            # End of quarter
            quarter = (start_date.month - 1) // 3
            month = (quarter + 1) * 3
            if month > 12:
                return start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                return start_date.replace(month=month + 1, day=1) - timedelta(days=1)
        
        elif period_type == 'semester':
            # End of semester (6 months)
            if start_date.month <= 6:
                return start_date.replace(month=7, day=1) - timedelta(days=1)
            else:
                return start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        
        elif period_type == 'annual':
            # End of year
            return start_date.replace(year=start_date.year + 1, month=1, day=1) - timedelta(days=1)
        
        else:  # one_time
            return start_date
