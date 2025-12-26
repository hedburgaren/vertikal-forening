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
    fee_category_ids = fields.Many2many(
        'vf.fee.category',
        string='Fee Categories'
    )
    min_amount = fields.Float(
        string='Minimum Amount'
    )
    max_amount = fields.Float(
        string='Maximum Amount'
    )
    
    # Display options
    group_by = fields.Selection([
        ('member', 'Member'),
        ('category', 'Fee Category'),
        ('section', 'Section'),
        ('group', 'Group'),
        ('status', 'Payment Status'),
    ], string='Group By', default='member')
    
    # Computed fields
    member_count = fields.Integer(
        string='Member Count',
        compute='_compute_statistics'
    )
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_statistics'
    )
    paid_amount = fields.Float(
        string='Paid Amount',
        compute='_compute_statistics'
    )
    outstanding_amount = fields.Float(
        string='Outstanding Amount',
        compute='_compute_statistics'
    )
    
    # Active
    active = fields.Boolean(
        string='Active',
        default=True
    )

    @api.depends('show_overdue_only', 'date_range', 'section_ids', 'group_ids', 
                 'fee_category_ids', 'min_amount', 'max_amount')
    def _compute_statistics(self):
        for view in self:
            # Get fees based on filters
            domain = view._get_fee_domain()
            fees = self.env['vf.fee'].search(domain)
            
            # Calculate statistics
            members = fees.mapped('member_id')
            view.member_count = len(set(members.ids))
            view.total_amount = sum(fees.mapped('amount'))
            view.paid_amount = sum(fees.mapped('paid_amount'))
            view.outstanding_amount = sum(fees.mapped('remaining_amount'))

    def _get_fee_domain(self):
        """Build domain for fee search based on view filters"""
        self.ensure_one()
        domain = [('state', '!=', 'cancelled')]
        
        # Date range
        if self.date_range == 'current_year':
            current_year = fields.Date.today().year
            domain.append(('generate_date', '>=', f'{current_year}-01-01'))
            domain.append(('generate_date', '<=', f'{current_year}-12-31'))
        elif self.date_range == 'last_12_months':
            date_12_months = fields.Date.today() - datetime.timedelta(days=365)
            domain.append(('generate_date', '>=', date_12_months))
        elif self.date_range == 'custom' and self.date_from and self.date_to:
            domain.append(('generate_date', '>=', self.date_from))
            domain.append(('generate_date', '<=', self.date_to))
        
        # Status filters
        if self.show_overdue_only:
            domain.append(('state', '=', 'overdue'))
        if not self.show_partial_payments:
            domain.append(('paid_amount', '=', 0))
        
        # Amount filters
        if self.min_amount:
            domain.append(('amount', '>=', self.min_amount))
        if self.max_amount:
            domain.append(('amount', '<=', self.max_amount))
        
        # Category filter
        if self.fee_category_ids:
            domain.append(('category_id', 'in', self.fee_category_ids.ids))
        
        # Get member IDs from section/group filters
        member_ids = []
        if self.section_ids:
            members = self.env['vf.member'].search([
                ('group_membership_ids.group_id.section_id', 'in', self.section_ids.ids)
            ])
            member_ids.extend(members.ids)
        
        if self.group_ids:
            members = self.env['vf.member'].search([
                ('group_membership_ids.group_id', 'in', self.group_ids.ids)
            ])
            member_ids.extend(members.ids)
        
        if member_ids:
            domain.append(('member_id', 'in', list(set(member_ids))))
        
        return domain

    def action_view_payments(self):
        """Open payment list with view filters applied"""
        self.ensure_one()
        
        domain = self._get_fee_domain()
        
        # Build action
        action = self.env.ref('vf_membership_fees.vf_fee_action').read()[0]
        action['domain'] = domain
        action['context'] = {
            'default_payment_view_id': self.id,
            'search_default_group_by_' + self.group_by: 1,
        }
        action['name'] = self.name
        
        return action

    def action_send_reminders(self):
        """Send payment reminders to filtered members"""
        self.ensure_one()
        
        domain = self._get_fee_domain()
        domain.append(('state', 'in', ['pending', 'overdue']))
        domain.append(('remaining_amount', '>', 0))
        
        fees = self.env['vf.fee'].search(domain)
        members = fees.mapped('member_id')
        
        if not members:
            raise UserError(_('No members found matching the criteria for reminders.'))
        
        # Create reminder wizard
        return {
            'name': _('Send Payment Reminders'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.payment.reminder.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_member_ids': members.ids,
                'default_fee_ids': fees.ids,
                'default_payment_view_id': self.id,
            },
        }

    def action_export_excel(self):
        """Export payment view to Excel"""
        self.ensure_one()
        
        # Get fees
        domain = self._get_fee_domain()
        fees = self.env['vf.fee'].search(domain)
        
        if not fees:
            raise UserError(_('No payments found matching the criteria.'))
        
        # Generate Excel
        import base64
        import io
        import xlsxwriter
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet('Payments')
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4F81BD',
            'font_color': 'white',
            'border': 1,
        })
        
        # Write headers
        headers = ['Membership No', 'Member Name', 'Email', 'Phone', 
                  'Fee Category', 'Description', 'Amount', 'Paid', 'Remaining', 
                  'Due Date', 'Status']
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Write data
        row = 1
        for fee in fees:
            member = fee.member_id
            worksheet.write(row, 0, member.membership_number)
            worksheet.write(row, 1, member.partner_id.name)
            worksheet.write(row, 2, member.partner_id.email or '')
            worksheet.write(row, 3, member.partner_id.phone or '')
            worksheet.write(row, 4, fee.category_id.name)
            worksheet.write(row, 5, fee.name)
            worksheet.write(row, 6, fee.amount)
            worksheet.write(row, 7, fee.paid_amount)
            worksheet.write(row, 8, fee.remaining_amount)
            worksheet.write(row, 9, fee.due_date.strftime('%Y-%m-%d'))
            worksheet.write(row, 10, dict(fee._fields['state'].selection).get(fee.state))
            row += 1
        
        # Totals
        worksheet.write(row, 5, 'TOTAL', header_format)
        worksheet.write(row, 6, sum(fees.mapped('amount')))
        worksheet.write(row, 7, sum(fees.mapped('paid_amount')))
        worksheet.write(row, 8, sum(fees.mapped('remaining_amount')))
        
        workbook.close()
        output.seek(0)
        
        # Create attachment
        filename = f'payment_view_{self.name}_{fields.Date.today().strftime("%Y%m%d")}.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
