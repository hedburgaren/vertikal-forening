# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfSponsorshipLevel(models.Model):
    _name = 'vf.sponsorship.level'
    _description = 'Sponsorship Level'
    _order = 'sequence, name'

    name = fields.Char(
        string='Level Name',
        required=True,
        translate=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    # Financial
    default_amount = fields.Float(
        string='Default Amount',
        required=True,
        digits='Account'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    # Benefits
    benefit_ids = fields.Many2many(
        'vf.sponsorship.benefit',
        string='Benefits'
    )
    
    # Visibility options
    show_on_website = fields.Boolean(
        string='Show on Website',
        default=True
    )
    show_logo = fields.Boolean(
        string='Show Logo',
        default=True
    )
    logo_size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ], string='Logo Size', default='medium')
    
    # Additional perks
    max_representatives = fields.Integer(
        string='Max Event Representatives',
        help='Maximum number of representatives at sponsored events'
    )
    free_tickets = fields.Integer(
        string='Free Event Tickets',
        help='Number of free tickets to association events'
    )
    
    # Display settings
    color = fields.Char(
        string='Display Color',
        default='#003366'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Statistics
    sponsor_count = fields.Integer(
        string='Active Sponsors',
        compute='_compute_sponsor_count'
    )

    @api.depends('name')
    def _compute_sponsor_count(self):
        for level in self:
            level.sponsor_count = self.env['vf.sponsor'].search_count([
                ('sponsorship_level_id', '=', level.id),
                ('state', '=', 'active')
            ])


class VfSponsorshipBenefit(models.Model):
    _name = 'vf.sponsorship.benefit'
    _description = 'Sponsorship Benefit'
    _order = 'name'

    name = fields.Char(
        string='Benefit Name',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    category = fields.Selection([
        ('visibility', 'Visibility'),
        ('promotion', 'Promotion'),
        ('events', 'Events'),
        ('recognition', 'Recognition'),
        ('other', 'Other'),
    ], string='Category', default='visibility')
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
