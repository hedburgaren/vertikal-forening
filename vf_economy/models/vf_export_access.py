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
        ('quarterly', 'Quarterly'),
    ], string='Frequency')
    schedule_day = fields.Integer(
        string='Day of Month',
        help='For monthly/quarterly: 1-31',
        default=1
    )
    schedule_hour = fields.Integer(
        string='Hour',
        help='Hour of day (0-23)',
        default=8
    )
    
    # Recipients
    recipient_ids = fields.Many2many(
        'res.partner',
        string='Email Recipients',
        help='Who receives the scheduled export'
    )
    
    # Last export info
    last_export_date = fields.Datetime(
        string='Last Export',
        readonly=True
    )
    last_export_user_id = fields.Many2one(
        'res.users',
        string='Last Exported By',
        readonly=True
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Computed fields
    next_export_date = fields.Datetime(
        compute='_compute_next_export_date',
        string='Next Export'
    )

    @api.depends('is_scheduled', 'schedule_frequency', 'last_export_date')
    def _compute_next_export_date(self):
        for access in self:
            if not access.is_scheduled:
                access.next_export_date = False
                continue
            
            from datetime import datetime, timedelta
            now = fields.Datetime.now()
            
            if access.schedule_frequency == 'daily':
                next_date = now + timedelta(days=1)
                next_date = next_date.replace(hour=access.schedule_hour, minute=0, second=0)
            elif access.schedule_frequency == 'weekly':
                next_date = now + timedelta(days=7)
                next_date = next_date.replace(hour=access.schedule_hour, minute=0, second=0)
            elif access.schedule_frequency == 'monthly':
                if now.day >= access.schedule_day:
                    # Next month
                    if now.month == 12:
                        next_date = datetime(now.year + 1, 1, access.schedule_day)
                    else:
                        next_date = datetime(now.year, now.month + 1, access.schedule_day)
                else:
                    # This month
                    next_date = datetime(now.year, now.month, access.schedule_day)
                next_date = next_date.replace(hour=access.schedule_hour, minute=0, second=0)
            elif access.schedule_frequency == 'quarterly':
                # Find next quarter
                current_quarter = (now.month - 1) // 3 + 1
                if current_quarter == 4:
                    next_quarter = 1
                    next_year = now.year + 1
                else:
                    next_quarter = current_quarter + 1
                    next_year = now.year
                
                next_month = (next_quarter - 1) * 3 + 1
                next_date = datetime(next_year, next_month, access.schedule_day)
                next_date = next_date.replace(hour=access.schedule_hour, minute=0, second=0)
            else:
                next_date = False
            
            access.next_export_date = next_export_date

    def check_access(self):
        """Check if current user can access this export"""
        self.ensure_one()
        
        # Check if user is in allowed users
        if self.allowed_user_ids and self.env.user in self.allowed_user_ids:
            return True
        
        # Check if user is in allowed groups
        if self.allowed_group_ids:
            user_groups = self.env.user.groups_id
            if any(group in user_groups for group in self.allowed_group_ids):
                return True
        
        # Check if user is treasurer or admin
        if self.env.user.has_group('vf_base.vf_treasurer') or \
           self.env.user.has_group('vf_base.vf_admin'):
            return True
        
        return False

    def action_export_now(self):
        """Generate and download the export"""
        self.ensure_one()
        
        if not self.check_access():
            raise UserError(_('You do not have permission to access this export.'))
        
        # Generate the report
        if self.report_type == 'revenue':
            attachment = self._generate_revenue_export()
        elif self.report_type == 'payment_status':
            attachment = self._generate_payment_status_export()
        elif self.report_type == 'age_analysis':
            attachment = self._generate_age_analysis_export()
        elif self.report_type == 'member_list':
            attachment = self._generate_member_list_export()
        elif self.report_type == 'attendance_report':
            attachment = self._generate_attendance_export()
        else:
            raise UserError(_('Unknown report type.'))
        
        # Update last export info
        self.write({
            'last_export_date': fields.Datetime.now(),
            'last_export_user_id': self.env.user.id,
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

    def _generate_revenue_export(self):
        """Generate revenue report export (PDF only)"""
        # Similar to economy report but without raw data access
        data = self._get_revenue_data()
        
        # Generate PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        import io
        import base64
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(inch, 10.5 * inch, "Revenue Report")
        
        # Period
        p.setFont("Helvetica", 12)
        p.drawString(inch, 10 * inch, f"Period: {data['period']}")
        
        # Summary
        y = 9 * inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(inch, y, "Summary:")
        y -= 0.3 * inch
        
        p.setFont("Helvetica", 10)
        p.drawString(inch + 0.5 * inch, y, f"Total Revenue: {data['total_revenue']:,.2f}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"Total Paid: {data['total_paid']:,.2f}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"Total Outstanding: {data['total_outstanding']:,.2f}")
        
        # Categories
        y -= 0.5 * inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(inch, y, "By Category:")
        y -= 0.3 * inch
        
        p.setFont("Helvetica", 10)
        for category, values in data['categories'].items():
            if y < 2 * inch:
                p.showPage()
                y = 10 * inch
            
            p.drawString(inch + 0.5 * inch, y, f"{category}: {values['total']:,.2f}")
            y -= 0.2 * inch
        
        p.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create attachment
        filename = f'revenue_report_{fields.Date.today().strftime("%Y%m%d")}.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return attachment

    def _generate_payment_status_export(self):
        """Generate payment status export (PDF only)"""
        data = self._get_payment_status_data()
        
        # Generate PDF similar to revenue export
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        import io
        import base64
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(inch, 10.5 * inch, "Payment Status Report")
        
        # Period
        p.setFont("Helvetica", 12)
        p.drawString(inch, 10 * inch, f"Period: {data['period']}")
        
        # Summary
        y = 9 * inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(inch, y, "Summary:")
        y -= 0.3 * inch
        
        p.setFont("Helvetica", 10)
        summary = data['summary']
        p.drawString(inch + 0.5 * inch, y, f"Total Members: {summary['total_members']}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"Fully Paid: {summary['fully_paid']}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"Partially Paid: {summary['partially_paid']}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"Not Paid: {summary['not_paid']}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"Overdue: {summary['overdue']}")
        
        p.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create attachment
        filename = f'payment_status_{fields.Date.today().strftime("%Y%m%d")}.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return attachment

    def _generate_age_analysis_export(self):
        """Generate age analysis export (PDF only)"""
        data = self._get_age_analysis_data()
        
        # Generate PDF
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        import io
        import base64
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(inch, 10.5 * inch, "Age Analysis Report")
        
        # Date
        p.setFont("Helvetica", 12)
        p.drawString(inch, 10 * inch, f"As of: {data['as_of_date']}")
        
        # Buckets
        y = 9 * inch
        p.setFont("Helvetica-Bold", 12)
        p.drawString(inch, y, "Aging Buckets:")
        y -= 0.3 * inch
        
        p.setFont("Helvetica", 10)
        buckets = data['aging_buckets']
        p.drawString(inch + 0.5 * inch, y, f"Current (0-30 days): {buckets['current']['count']} members, {buckets['current']['amount']:,.2f}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"31-60 days: {buckets['30_60']['count']} members, {buckets['30_60']['amount']:,.2f}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"61-90 days: {buckets['60_90']['count']} members, {buckets['60_90']['amount']:,.2f}")
        y -= 0.2 * inch
        p.drawString(inch + 0.5 * inch, y, f"90+ days: {buckets['90_plus']['count']} members, {buckets['90_plus']['amount']:,.2f}")
        y -= 0.3 * inch
        p.drawString(inch + 0.5 * inch, y, f"Total Outstanding: {data['total_outstanding']:,.2f}")
        
        p.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create attachment
        filename = f'age_analysis_{fields.Date.today().strftime("%Y%m%d")}.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return attachment

    def _generate_member_list_export(self):
        """Generate member list export (PDF only)"""
        members = self.env['vf.member'].search([('status', '=', 'active')])
        
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        import io
        import base64
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(inch, 10.5 * inch, "Member List")
        
        # Date
        p.setFont("Helvetica", 12)
        p.drawString(inch, 10 * inch, f"As of: {fields.Date.today()}")
        
        # Members
        y = 9 * inch
        p.setFont("Helvetica-Bold", 10)
        p.drawString(inch, y, "Membership No")
        p.drawString(inch + 2 * inch, y, "Name")
        p.drawString(inch + 4 * inch, y, "Email")
        y -= 0.2 * inch
        
        p.setFont("Helvetica", 9)
        for member in members:
            if y < 2 * inch:
                p.showPage()
                y = 10 * inch
            
            p.drawString(inch, y, member.membership_number)
            p.drawString(inch + 2 * inch, y, member.partner_id.name[:30])
            p.drawString(inch + 4 * inch, y, member.partner_id.email or ''[:30])
            y -= 0.15 * inch
        
        p.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create attachment
        filename = f'member_list_{fields.Date.today().strftime("%Y%m%d")}.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return attachment

    def _generate_attendance_export(self):
        """Generate attendance report export (PDF only)"""
        # Placeholder implementation
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        import io
        import base64
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        
        # Title
        p.setFont("Helvetica-Bold", 16)
        p.drawString(inch, 10.5 * inch, "Attendance Report")
        
        # Message
        p.setFont("Helvetica", 12)
        p.drawString(inch, 9 * inch, "Attendance report requires activity module integration.")
        
        p.save()
        pdf_content = buffer.getvalue()
        buffer.close()
        
        # Create attachment
        filename = f'attendance_report_{fields.Date.today().strftime("%Y%m%d")}.pdf'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
            'res_model': self._name,
            'res_id': self.id,
        })
        
        return attachment

    # Helper methods to get data (similar to economy report)
    def _get_revenue_data(self):
        """Get revenue data for export"""
        # Simplified version - similar to economy report
        return {
            'period': f'{fields.Date.today().replace(month=1, day=1)} - {fields.Date.today()}',
            'categories': {},
            'total_revenue': 0,
            'total_paid': 0,
            'total_outstanding': 0,
        }

    def _get_payment_status_data(self):
        """Get payment status data for export"""
        return {
            'period': f'{fields.Date.today().replace(month=1, day=1)} - {fields.Date.today()}',
            'summary': {
                'total_members': 0,
                'fully_paid': 0,
                'partially_paid': 0,
                'not_paid': 0,
                'overdue': 0,
            }
        }

    def _get_age_analysis_data(self):
        """Get age analysis data for export"""
        return {
            'as_of_date': fields.Date.today(),
            'aging_buckets': {
                'current': {'count': 0, 'amount': 0},
                '30_60': {'count': 0, 'amount': 0},
                '60_90': {'count': 0, 'amount': 0},
                '90_plus': {'count': 0, 'amount': 0},
            },
            'total_outstanding': 0,
        }

    @api.model
    def run_scheduled_exports(self):
        """Cron job to run scheduled exports"""
        today = fields.Datetime.now()
        
        exports = self.search([
            ('is_scheduled', '=', True),
            ('active', '=', True),
            ('next_export_date', '<=', today),
        ])
        
        for export in exports:
            try:
                attachment = export.action_export_now()
                
                # Send email to recipients
                if export.recipient_ids:
                    template = self.env.ref('vf_economy.email_template_scheduled_export')
                    for recipient in export.recipient_ids:
                        template.send_mail(
                            export.id,
                            email_values={
                                'email_to': recipient.email,
                                'attachment_ids': [(4, attachment.id)],
                            }
                        )
                
                # Update next export date
                export._compute_next_export_date()
                
            except Exception as e:
                # Log error but continue with other exports
                self.env['mail.message'].create({
                    'model': export._name,
                    'res_id': export.id,
                    'message_type': 'notification',
                    'body': f'Scheduled export failed: {str(e)}',
                })
