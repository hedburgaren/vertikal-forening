# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VfMandateExtension(models.Model):
    _name = 'vf.mandate.extension'
    _description = 'Mandate Extension'
    _order = 'approval_date desc'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    mandate_id = fields.Many2one(
        'vf.mandate',
        string='Mandate',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Extension details
    original_end_date = fields.Date(
        string='Original End Date',
        required=True,
        readonly=True,
        tracking=True
    )
    new_end_date = fields.Date(
        string='New End Date',
        required=True,
        tracking=True
    )
    
    # Approval
    extension_reason = fields.Text(
        string='Extension Reason',
        required=True,
        tracking=True
    )
    approved_by = fields.Many2one(
        'res.partner',
        string='Approved By',
        required=True,
        tracking=True,
        domain=[('is_company', '=', False)]
    )
    approval_date = fields.Date(
        string='Approval Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    )
    
    # Status
    status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', default='pending', required=True, tracking=True)
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    _sql_constraints = [
        ('dates_check', 'CHECK(new_end_date > original_end_date)', 
         'New end date must be after original end date!'),
    ]

    @api.depends('mandate_id', 'original_end_date', 'new_end_date')
    def _compute_display_name(self):
        for extension in self:
            extension.display_name = (
                f'Extension for {extension.mandate_id.display_name}: '
                f'{extension.original_end_date} → {extension.new_end_date}'
            )

    @api.constrains('new_end_date')
    def _check_new_end_date(self):
        for extension in self:
            if extension.new_end_date <= extension.original_end_date:
                raise ValidationError(_('New end date must be after original end date.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'mandate_id' in vals:
                mandate = self.env['vf.mandate'].browse(vals['mandate_id'])
                vals['original_end_date'] = mandate.end_date
        return super().create(vals_list)

    def action_approve(self):
        """Approve the extension and update the mandate"""
        for extension in self:
            extension.write({'status': 'approved'})
            extension.mandate_id.write({'end_date': extension.new_end_date})
        return True

    def action_reject(self):
        """Reject the extension"""
        self.write({'status': 'rejected'})
        return True
