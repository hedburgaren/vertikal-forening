# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfFeeCategory(models.Model):
    _name = 'vf.fee.category'
    _description = 'Fee Category'
    _order = 'sequence, name'

    # Core fields
    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True
    )
    code = fields.Char(
        string='Code',
        required=True,
        help='Unique code for programmatic reference'
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    
    # Configuration
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    active = fields.Boolean(
        default=True
    )
    
    # Fee structure
    amount = fields.Float(
        string='Amount',
        required=True,
        digits='Account'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    # Period settings
    period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semester', 'Semester'),
        ('annual', 'Annual'),
        ('one_time', 'One Time'),
    ], string='Period Type', required=True, default='annual')
    
    # Age restrictions
    min_age = fields.Integer(
        string='Minimum Age',
        help='Minimum age to apply this category'
    )
    max_age = fields.Integer(
        string='Maximum Age',
        help='Maximum age to apply this category (0 = no limit)'
    )
    
    # Member type restrictions
    member_type = fields.Selection([
        ('all', 'All Members'),
        ('regular', 'Regular Members'),
        ('student', 'Student Members'),
        ('senior', 'Senior Members'),
        ('family', 'Family Members'),
        ('youth', 'Youth Members'),
    ], string='Member Type', default='all', required=True)
    
    # Group/section restrictions
    group_ids = fields.Many2many(
        'vf.group',
        'vf_fee_category_group_rel',
        'category_id',
        'group_id',
        string='Applicable Groups',
        help='Leave empty to apply to all groups'
    )
    section_ids = fields.Many2many(
        'vf.section',
        'vf_fee_category_section_rel',
        'category_id',
        'section_id',
        string='Applicable Sections',
        help='Leave empty to apply to all sections'
    )
    
    # Auto-generation settings
    auto_generate = fields.Boolean(
        string='Auto Generate Fees',
        default=True,
        help='Automatically generate fees for eligible members'
    )
    generate_day = fields.Integer(
        string='Generate Day',
        default=1,
        help='Day of month to generate fees (1-31)'
    )
    
    # Payment settings
    due_days = fields.Integer(
        string='Payment Due Days',
        default=30,
        help='Number of days after generation when payment is due'
    )
    allow_partial_payment = fields.Boolean(
        string='Allow Partial Payment',
        default=False
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'The code must be unique!'),
        ('check_age_range', 'CHECK(max_age = 0 OR max_age > min_age)', 
         'Maximum age must be greater than minimum age!'),
        ('check_generate_day', 'CHECK(generate_day >= 1 AND generate_day <= 31)', 
         'Generate day must be between 1 and 31!'),
    ]

    def name_get(self):
        result = []
        for category in self:
            name = category.name
            if category.amount:
                name = f'{name} ({category.amount} {category.currency_id.symbol})'
            result.append((category.id, name))
        return result

    @api.model
    def get_applicable_categories(self, member):
        """Get fee categories applicable to a member"""
        domain = [
            ('active', '=', True),
            '|', ('member_type', '=', 'all'), ('member_type', '=', member.member_type),
        ]
        
        # Age restrictions
        if member.age:
            age_domain = [
                '|', ('min_age', '=', 0), ('min_age', '<=', member.age),
                '|', ('max_age', '=', 0), ('max_age', '>=', member.age),
            ]
            domain.extend(age_domain)
        
        # Group/section restrictions
        if member.group_ids:
            domain.append('|')
            domain.append(('group_ids', 'in', member.group_ids.ids))
            domain.append(('group_ids', '=', False))
        else:
            domain.append(('group_ids', '=', False))
        
        if member.section_ids:
            domain.append('|')
            domain.append(('section_ids', 'in', member.section_ids.ids))
            domain.append(('section_ids', '=', False))
        else:
            domain.append(('section_ids', '=', False))
        
        return self.search(domain)
