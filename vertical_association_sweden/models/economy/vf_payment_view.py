# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class VfPaymentView(models.Model):
    _name = 'vf.payment.view'
    _description = 'Payment View Configuration'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='View Name',
        required=True
    )
    description = fields.Text(
        string='Description'
    )
    
    # View configuration
    show_overdue_only = fields.Boolean(
        string='Show Overdue Only',
        default=False,
        help='Only show members with overdue payments'
    )
    show_partial_payments = fields.Boolean(
        string='Show Partial Payments',
        default=True,
        help='Show members who have paid partially'
    )
    date_range = fields.Selection([
        ('all', 'All Time'),
        ('current_year', 'Current Year'),
        ('last_12_months', 'Last 12 Months'),
        ('custom', 'Custom Range'),
    ], string='Date Range', default='current_year')
    date_from = fields.Date(
        string='From Date'
    )
    date_to = fields.Date(
        string='To Date'
    )
    
    # Filters
    section_ids = fields.Many2many(
        'vf.section',
        string='Sections'
    )
    group_ids = fields.Many2many(
        'vf.group',
        string='Groups'
    )
    fee_type_ids = fields.Many2many(
        'vf.fee.type',
        string='Fee Types'
    )
    
    # Display options
    group_by = fields.Selection([
        ('member', 'Member'),
        ('section', 'Section'),
        ('group', 'Group'),
        ('fee_type', 'Fee Type'),
    ], string='Group By', default='member')
    show_details = fields.Boolean(
        string='Show Details',
        default=True,
        help='Show individual fee lines'
    )
    
    # Computed fields
    member_count = fields.Integer(
        string='Member Count',
        compute='_compute_statistics'
    )
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_statistics'
    )
    total_paid = fields.Float(
        string='Total Paid',
        compute='_compute_statistics'
    )
    total_outstanding = fields.Float(
        string='Total Outstanding',
        compute='_compute_statistics'
    )

    @api.depends('show_overdue_only', 'date_range', 'date_from', 'date_to', 
                 'section_ids', 'group_ids', 'fee_type_ids')
    def _compute_statistics(self):
        for view in self:
            fees = view._get_fees()
            
            # Calculate statistics
            members = fees.mapped('member_id')
            view.member_count = len(members)
            view.total_amount = sum(fees.mapped('amount'))
            view.total_paid = sum(fees.mapped('paid_amount'))
            view.total_outstanding = sum(fees.mapped('remaining_amount'))

    def _get_fees(self):
        """Get fees based on view configuration"""
        self.ensure_one()
        
        # Base domain
        domain = [('state', '!=', 'cancelled')]
        
        # Date filter
        if self.date_range == 'current_year':
            current_year = fields.Date.today().year
            domain.extend([
                ('date_due', '>=', f'{current_year}-01-01'),
                ('date_due', '<=', f'{current_year}-12-31')
            ])
        elif self.date_range == 'last_12_months':
            date_12_months = fields.Date.today() - datetime.timedelta(days=365)
            domain.append(('date_due', '>=', date_12_months))
        elif self.date_range == 'custom' and self.date_from and self.date_to:
            domain.extend([
                ('date_due', '>=', self.date_from),
                ('date_due', '<=', self.date_to)
            ])
        
        # Status filter
        if self.show_overdue_only:
            domain.append(('state', '=', 'overdue'))
        elif not self.show_partial_payments:
            domain.append(('state', 'in', ['pending', 'overdue']))
        
        # Section filter
        if self.section_ids:
            domain.append(('member_id.group_ids.section_id', 'in', self.section_ids.ids))
        
        # Group filter
        if self.group_ids:
            domain.append(('member_id.group_ids', 'in', self.group_ids.ids))
        
        # Fee type filter
        if self.fee_type_ids:
            domain.append(('fee_type_id', 'in', self.fee_type_ids.ids))
        
        return self.env['vf.fee'].search(domain)

    def action_view_members(self):
        """View members matching this view"""
        self.ensure_one()
        
        fees = self._get_fees()
        members = fees.mapped('member_id')
        
        action = self.env.ref('vertical_association_sweden.vf_member_action').read()[0]
        action['domain'] = [('id', 'in', members.ids)]
        return action

    def action_view_fees(self):
        """View fees matching this view"""
        self.ensure_one()
        
        fees = self._get_fees()
        
        action = self.env.ref('vertical_association_sweden.vf_fee_action').read()[0]
        action['domain'] = [('id', 'in', fees.ids)]
        return action

    def action_export_excel(self):
        """Export view to Excel"""
        self.ensure_one()
        
        fees = self._get_fees()
        
        # Create Excel file
        import xlsxwriter
        import io
        import base64
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Payment View')
        
        # Headers
        headers = ['Member', 'Membership Number', 'Section', 'Group', 
                  'Fee Type', 'Date Due', 'Amount', 'Paid', 'Outstanding', 'Status']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header)
        
        # Data
        row = 1
        for fee in fees:
            member = fee.member_id
            worksheet.write(row, 0, member.name or '')
            worksheet.write(row, 1, member.membership_number or '')
            worksheet.write(row, 2, member.group_ids[0].section_id.name if member.group_ids else '')
            worksheet.write(row, 3, ', '.join(member.group_ids.mapped('name')))
            worksheet.write(row, 4, fee.fee_type_id.name or '')
            worksheet.write(row, 5, fee.date_due or '')
            worksheet.write(row, 6, fee.amount or 0)
            worksheet.write(row, 7, fee.paid_amount or 0)
            worksheet.write(row, 8, fee.remaining_amount or 0)
            worksheet.write(row, 9, fee.state or '')
            row += 1
        
        workbook.close()
        output.seek(0)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}.xlsx',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def action_send_reminders(self):
        """Send payment reminders to all members in view"""
        self.ensure_one()
        
        fees = self._get_fees().filtered(
            lambda f: f.state in ['pending', 'overdue'] and f.remaining_amount > 0
        )
        
        if not fees:
            raise UserError(_('No members with outstanding payments found.'))
        
        members = fees.mapped('member_id')
        
        return {
            'name': _('Send Payment Reminders'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.payment.reminder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_member_ids': [(6, 0, members.ids)],
                'default_fee_ids': [(6, 0, fees.ids)],
            },
        }
