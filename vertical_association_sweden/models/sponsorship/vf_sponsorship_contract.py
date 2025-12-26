# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfSponsorshipContract(models.Model):
    _name = 'vf.sponsorship.contract'
    _description = 'Sponsorship Contract'
    _order = 'start_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    sponsor_id = fields.Many2one(
        'vf.sponsor',
        string='Sponsor',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Contract details
    contract_number = fields.Char(
        string='Contract Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    type = fields.Selection([
        ('initial', 'Initial'),
        ('renewal', 'Renewal'),
        ('amendment', 'Amendment'),
    ], string='Contract Type', required=True, default='initial')
    
    # Dates
    start_date = fields.Date(
        string='Start Date',
        required=True,
        tracking=True
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
        tracking=True
    )
    signed_date = fields.Date(
        string='Signed Date',
        tracking=True
    )
    
    # Financial terms
    amount = fields.Float(
        string='Contract Amount',
        required=True,
        tracking=True,
        digits='Account'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    payment_schedule = fields.Selection([
        ('annual', 'Annual'),
        ('semi_annual', 'Semi-Annual'),
        ('quarterly', 'Quarterly'),
        ('monthly', 'Monthly'),
        ('lump_sum', 'Lump Sum'),
    ], string='Payment Schedule', default='annual')
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('signed', 'Signed'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Contract document
    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Contract Document',
        tracking=True
    )
    
    # Signatories
    signed_by = fields.Many2one(
        'res.partner',
        string='Signed By',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    company_signatory_id = fields.Many2one(
        'res.partner',
        string='Company Signatory',
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    
    # Terms and conditions
    terms = fields.Html(
        string='Terms and Conditions',
        tracking=True
    )
    special_conditions = fields.Text(
        string='Special Conditions',
        tracking=True
    )
    
    # Benefits
    benefit_ids = fields.Many2many(
        'vf.sponsorship.benefit',
        string='Contract Benefits'
    )
    custom_benefits = fields.Text(
        string='Custom Benefits',
        tracking=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    is_active = fields.Boolean(
        compute='_compute_is_active',
        store=True
    )
    days_remaining = fields.Integer(
        compute='_compute_days_remaining',
        string='Days Remaining'
    )

    @api.depends('contract_number', 'sponsor_id')
    def _compute_display_name(self):
        for contract in self:
            contract.display_name = f'{contract.contract_number} - {contract.sponsor_id.name}'

    @api.depends('state', 'start_date', 'end_date')
    def _compute_is_active(self):
        today = fields.Date.today()
        for contract in self:
            contract.is_active = (
                contract.state in ['signed', 'active'] and
                contract.start_date <= today <= contract.end_date
            )

    @api.depends('end_date', 'state')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for contract in self:
            if contract.state in ['signed', 'active'] and contract.end_date:
                contract.days_remaining = (contract.end_date - today).days
            else:
                contract.days_remaining = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('contract_number', _('New')) == _('New'):
                vals['contract_number'] = self._generate_contract_number()
        return super().create(vals_list)

    def _generate_contract_number(self):
        """Generate a unique contract number"""
        sequence = self.env['ir.sequence'].next_by_code('vf.sponsorship.contract') or '0000'
        return f'SP-{sequence}'

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for contract in self:
            if contract.start_date >= contract.end_date:
                raise ValidationError(_('End date must be after start date.'))

    @api.constrains('sponsor_id', 'start_date', 'end_date')
    def _check_overlap(self):
        for contract in self:
            if contract.state not in ['draft', 'terminated']:
                overlapping = self.search([
                    ('sponsor_id', '=', contract.sponsor_id.id),
                    ('state', 'in', ['signed', 'active']),
                    ('id', '!=', contract.id),
                    '|', '|',
                    ('start_date', '<=', contract.start_date),
                    ('end_date', '>=', contract.start_date),
                    ('start_date', '<=', contract.end_date),
                    ('end_date', '>=', contract.end_date),
                ])
                if overlapping:
                    raise ValidationError(_('Contract dates overlap with existing contract.'))

    def action_send(self):
        """Send contract to sponsor"""
        self.write({'state': 'sent'})
        return True

    def action_sign(self):
        """Mark contract as signed"""
        self.write({
            'state': 'signed',
            'signed_date': fields.Date.today(),
            'signed_by': self.env.user.partner_id.id,
        })
        return True

    def action_activate(self):
        """Activate the contract"""
        self.write({'state': 'active'})
        return True

    def action_terminate(self):
        """Terminate the contract"""
        self.write({'state': 'terminated'})
        return True

    def action_generate_document(self):
        """Generate contract document"""
        self.ensure_one()
        return {
            'name': _('Generate Contract'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.contract.document.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_contract_id': self.id},
        }

    def action_send_reminder(self):
        """Send payment reminder"""
        self.ensure_one()
        if self.state != 'active':
            raise ValidationError(_('Only active contracts can send payment reminders.'))
        
        template = self.env.ref('vertical_association_sweden.email_template_sponsor_payment_reminder')
        template.send_mail(self.id, force_send=True)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Reminder Sent'),
                'message': _('Payment reminder has been sent to the sponsor.'),
                'type': 'success',
            }
        }
