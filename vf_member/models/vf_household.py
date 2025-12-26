# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfHousehold(models.Model):
    _name = 'vf.household'
    _description = 'Household Grouping'
    _order = 'name'
    _rec_name = 'display_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Household Name',
        tracking=True,
        help='Optional name for the household (e.g., "The Smith Family")'
    )
    address_id = fields.Many2one(
        'res.partner',
        string='Address',
        tracking=True,
        domain=[('is_company', '=', True)],
        help='The address partner for this household'
    )
    
    # Member relationships
    member_ids = fields.One2many(
        'vf.member',
        'household_id',
        string='Members',
        tracking=True
    )
    member_count = fields.Integer(
        string='Member Count',
        compute='_compute_member_count',
        store=True
    )
    
    # Contact information
    phone = fields.Char(
        string='Phone',
        related='address_id.phone',
        readonly=False
    )
    email = fields.Char(
        string='Email',
        related='address_id.email',
        readonly=False
    )
    street = fields.Char(
        related='address_id.street',
        readonly=False
    )
    street2 = fields.Char(
        related='address_id.street2',
        readonly=False
    )
    city = fields.Char(
        related='address_id.city',
        readonly=False
    )
    state_id = fields.Many2one(
        'res.country.state',
        related='address_id.state_id',
        readonly=False
    )
    zip = fields.Char(
        related='address_id.zip',
        readonly=False
    )
    country_id = fields.Many2one(
        'res.country',
        related='address_id.country_id',
        readonly=False
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    
    # Active flag for archiving
    active = fields.Boolean(
        default=True,
        tracking=True
    )

    @api.depends('name', 'address_id')
    def _compute_display_name(self):
        for household in self:
            if household.name:
                household.display_name = household.name
            elif household.address_id:
                household.display_name = f'Household - {household.address_id.name or household.address_id.street or "Unnamed"}'
            else:
                household.display_name = 'Unnamed Household'

    @api.depends('member_ids')
    def _compute_member_count(self):
        for household in self:
            household.member_count = len(household.member_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Create address partner if not provided
            if not vals.get('address_id') and (vals.get('street') or vals.get('name')):
                address_vals = {
                    'is_company': True,
                    'name': vals.get('name', 'Household Address'),
                    'street': vals.get('street'),
                    'street2': vals.get('street2'),
                    'city': vals.get('city'),
                    'state_id': vals.get('state_id'),
                    'zip': vals.get('zip'),
                    'country_id': vals.get('country_id'),
                    'phone': vals.get('phone'),
                    'email': vals.get('email'),
                }
                address = self.env['res.partner'].create(address_vals)
                vals['address_id'] = address.id
        return super().create(vals_list)

    def write(self, vals):
        # Update address partner if address fields are changed
        address_fields = ['street', 'street2', 'city', 'state_id', 'zip', 'country_id', 'phone', 'email']
        if any(field in vals for field in address_fields):
            for household in self:
                if household.address_id:
                    address_vals = {field: vals[field] for field in address_fields if field in vals}
                    household.address_id.write(address_vals)
        return super().write(vals)

    def action_view_members(self):
        """Open member view with this household's members"""
        self.ensure_one()
        action = self.env.ref('vf_member.vf_member_action').read()[0]
        action['domain'] = [('household_id', '=', self.id)]
        action['context'] = {'default_household_id': self.id}
        return action

    def action_create_address(self):
        """Create or update the address partner"""
        for household in self:
            if not household.address_id:
                address_vals = {
                    'is_company': True,
                    'name': household.name or 'Household Address',
                }
                address = self.env['res.partner'].create(address_vals)
                household.address_id = address.id
        return True
