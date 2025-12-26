# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class VfExportAccess(models.Model):
    _name = 'vf.export.access'
    _description = 'Export Access Configuration'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Report Name',
        required=True
    )
    description = fields.Text(
        string='Description'
    )
    
    # Report configuration
    report_type = fields.Selection([
        ('revenue', 'Revenue Report'),
        ('payment_status', 'Payment Status Report'),
        ('age_analysis', 'Age Analysis Report'),
        ('member_list', 'Member List'),
        ('attendance_report', 'Attendance Report'),
    ], string='Report Type', required=True)
    
    # Access control
    allowed_user_ids = fields.Many2one(
        'res.users',
        string='Allowed Users',
        help='Users who can access this export'
    )
    allowed_group_ids = fields.Many2one(
        'res.groups',
        string='Allowed Groups',
        help='Groups that can access this export'
    )
    
    # Schedule
    is_scheduled = fields.Boolean(
        string='Scheduled Export',
        default=False
    )
    schedule_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], string='Frequency')
    schedule_day = fields.Integer(
        string='Day of Month',
        help='For monthly exports (1-31)'
    )
    schedule_time = fields.Float(
        string='Time (24h)',
        help='Time in 24-hour format (e.g., 14.5 for 14:30)'
    )
    
    # Export settings
    export_format = fields.Selection([
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
    ], string='Export Format', default='excel')
    
    # Email settings
    auto_email = fields.Boolean(
        string='Auto Email',
        default=False
    )
    email_to = fields.Char(
        string='Email To',
        help='Comma-separated email addresses'
    )
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template'
    )
    
    # Status
    active = fields.Boolean(
        default=True
    )
    last_export = fields.Datetime(
        string='Last Export',
        readonly=True
    )
    next_export = fields.Datetime(
        string='Next Export',
        compute='_compute_next_export',
        store=True
    )
    
    # Statistics
    export_count = fields.Integer(
        string='Export Count',
        default=0
    )

    @api.depends('is_scheduled', 'schedule_frequency', 'schedule_day', 
                 'schedule_time', 'last_export')
    def _compute_next_export(self):
        for export in self:
            if not export.is_scheduled:
                export.next_export = False
                continue
            
            from datetime import datetime, timedelta
            
            now = fields.Datetime.now()
            if export.last_export:
                base_date = export.last_export
            else:
                base_date = now
            
            if export.schedule_frequency == 'daily':
                next_date = base_date + timedelta(days=1)
            elif export.schedule_frequency == 'weekly':
                next_date = base_date + timedelta(weeks=1)
            elif export.schedule_frequency == 'monthly':
                # Add month
                month = base_date.month - 1 + 1
                year = base_date.year + month // 12
                month = month % 12 + 1
                day = min(export.schedule_day or base_date.day, 28)  # Avoid invalid dates
                next_date = base_date.replace(year=year, month=month, day=day)
            else:
                next_date = False
            
            # Set time
            if next_date and export.schedule_time:
                hours = int(export.schedule_time)
                minutes = int((export.schedule_time - hours) * 60)
                next_date = next_date.replace(hour=hours, minute=minutes, second=0)
            
            export.next_export = next_date

    def check_access(self):
        """Check if current user can access this export"""
        self.ensure_one()
        
        user = self.env.user
        
        # Check if user is in allowed users
        if user in self.allowed_user_ids:
            return True
        
        # Check if user is in allowed groups
        if any(group in user.groups_id for group in self.allowed_group_ids):
            return True
        
        return False

    def action_export(self):
        """Generate the export"""
        self.ensure_one()
        
        if not self.check_access():
            raise UserError(_('You do not have permission to access this export.'))
        
        try:
            if self.report_type == 'revenue':
                result = self._export_revenue()
            elif self.report_type == 'payment_status':
                result = self._export_payment_status()
            elif self.report_type == 'age_analysis':
                result = self._export_age_analysis()
            elif self.report_type == 'member_list':
                result = self._export_member_list()
            elif self.report_type == 'attendance_report':
                result = self._export_attendance_report()
            else:
                raise UserError(_('Unknown report type.'))
            
            # Update statistics
            self.write({
                'last_export': fields.Datetime.now(),
                'export_count': self.export_count + 1,
            })
            
            # Auto email if enabled
            if self.auto_email and self.email_to:
                self._send_email(result)
            
            return result
            
        except Exception as e:
            raise UserError(_('Error generating export: %s') % str(e))

    def _export_revenue(self):
        """Export revenue report"""
        # Implementation would generate the revenue report
        pass

    def _export_payment_status(self):
        """Export payment status report"""
        # Implementation would generate the payment status report
        pass

    def _export_age_analysis(self):
        """Export age analysis report"""
        # Implementation would generate the age analysis report
        pass

    def _export_member_list(self):
        """Export member list"""
        # Implementation would generate the member list
        pass

    def _export_attendance_report(self):
        """Export attendance report"""
        # Implementation would generate the attendance report
        pass

    def _send_email(self, attachment_id):
        """Send export via email"""
        if not self.email_template_id:
            # Use default email
            mail_values = {
                'subject': f'Export: {self.name}',
                'body_html': f'<p>Please find attached the export: {self.name}</p>',
                'email_to': self.email_to,
                'attachment_ids': [(4, attachment_id)],
            }
            self.env['mail.mail'].create(mail_values).send()
        else:
            # Use template
            self.email_template_id.send_mail(
                self.id,
                force_send=True,
                email_values={
                    'email_to': self.email_to,
                    'attachment_ids': [(4, attachment_id)],
                }
            )

    @api.model
    def run_scheduled_exports(self):
        """Run all scheduled exports that are due"""
        now = fields.Datetime.now()
        
        due_exports = self.search([
            ('is_scheduled', '=', True),
            ('active', '=', True),
            ('next_export', '<=', now),
        ])
        
        for export in due_exports:
            try:
                export.action_export()
            except Exception as e:
                # Log error but continue with other exports
                _logger.error('Failed to run scheduled export %s: %s', 
                             export.name, str(e))
