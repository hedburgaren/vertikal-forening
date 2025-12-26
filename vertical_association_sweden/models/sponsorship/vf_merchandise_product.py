# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfMerchandiseCategory(models.Model):
    _name = 'vf.merchandise.category'
    _description = 'Merchandise Category'
    _order = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    parent_id = fields.Many2one(
        'vf.merchandise.category',
        string='Parent Category'
    )
    child_ids = fields.One2many(
        'vf.merchandise.category',
        'parent_id',
        string='Child Categories'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )


class VfMerchandiseProduct(models.Model):
    _name = 'vf.merchandise.product'
    _description = 'Merchandise Product'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    name = fields.Char(
        string='Product Name',
        required=True,
        tracking=True,
        translate=True
    )
    description = fields.Html(
        string='Description',
        tracking=True,
        translate=True
    )
    category_id = fields.Many2one(
        'vf.merchandise.category',
        string='Category',
        required=True,
        tracking=True
    )
    
    # Product details
    product_code = fields.Char(
        string='Product Code',
        required=True,
        tracking=True
    )
    variant_ids = fields.One2many(
        'vf.merchandise.variant',
        'product_id',
        string='Variants'
    )
    
    # Pricing
    list_price = fields.Float(
        string='List Price',
        required=True,
        tracking=True,
        digits='Product Price'
    )
    cost_price = fields.Float(
        string='Cost Price',
        tracking=True,
        digits='Product Price'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    # Inventory
    track_inventory = fields.Boolean(
        string='Track Inventory',
        default=True
    )
    stock_quantity = fields.Float(
        string='Stock Quantity',
        default=0,
        tracking=True
    )
    reorder_point = fields.Float(
        string='Reorder Point',
        help='When to reorder this product'
    )
    
    # Sponsorship integration
    sponsor_price = fields.Float(
        string='Sponsor Price',
        help='Special price for sponsors',
        digits='Product Price'
    )
    sponsorship_level_ids = fields.Many2many(
        'vf.sponsorship.level',
        string='Available to Levels',
        help='Sponsorship levels that can purchase this product'
    )
    
    # Media
    image = fields.Binary(
        string='Product Image',
        tracking=True
    )
    image_medium = fields.Binary(
        string='Medium-sized Image',
        compute='_compute_images',
        store=True
    )
    image_small = fields.Binary(
        string='Small-sized Image',
        compute='_compute_images',
        store=True
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    available_online = fields.Boolean(
        string='Available Online',
        default=True,
        tracking=True
    )
    
    # Computed fields
    variant_count = fields.Integer(
        string='Variant Count',
        compute='_compute_variant_count',
        store=True
    )
    total_stock = fields.Float(
        string='Total Stock',
        compute='_compute_total_stock',
        store=True
    )

    @api.depends('image')
    def _compute_images(self):
        for product in self:
            # Simple image resizing - in practice, use proper image processing
            product.image_medium = product.image
            product.image_small = product.image

    @api.depends('variant_ids')
    def _compute_variant_count(self):
        for product in self:
            product.variant_count = len(product.variant_ids)

    @api.depends('track_inventory', 'stock_quantity', 'variant_ids.stock_quantity')
    def _compute_total_stock(self):
        for product in self:
            if product.track_inventory:
                product.total_stock = product.stock_quantity + sum(
                    product.variant_ids.mapped('stock_quantity')
                )
            else:
                product.total_stock = 0

    @api.constrains('product_code')
    def _check_product_code(self):
        for product in self:
            existing = self.search([
                ('product_code', '=', product.product_code),
                ('id', '!=', product.id)
            ])
            if existing:
                raise ValidationError(_('Product code must be unique!'))

    def action_view_variants(self):
        """View product variants"""
        self.ensure_one()
        action = self.env.ref('vertical_association_sweden.vf_merchandise_variant_action').read()[0]
        action['domain'] = [('product_id', '=', self.id)]
        action['context'] = {'default_product_id': self.id}
        return action

    def action_create_variant(self):
        """Create a new variant"""
        self.ensure_one()
        return {
            'name': _('Create Variant'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.merchandise.variant',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id},
        }

    def action_update_stock(self):
        """Update stock levels"""
        self.ensure_one()
        return {
            'name': _('Update Stock'),
            'type': 'ir.actions.act_window',
            'res_model': 'vf.stock.update.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_product_id': self.id},
        }

    def get_price(self, partner_id=None):
        """Get price for a specific partner"""
        self.ensure_one()
        
        # Check if partner is a sponsor
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            sponsor = self.env['vf.sponsor'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'active')
            ], limit=1)
            
            if sponsor and sponsor.sponsorship_level_id in self.sponsorship_level_ids:
                return self.sponsor_price or self.list_price
        
        return self.list_price


class VfMerchandiseVariant(models.Model):
    _name = 'vf.merchandise.variant'
    _description = 'Merchandise Product Variant'
    _order = 'product_id, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    product_id = fields.Many2one(
        'vf.merchandise.product',
        string='Product',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    name = fields.Char(
        string='Variant Name',
        required=True,
        tracking=True
    )
    
    # Attributes
    attribute_ids = fields.One2many(
        'vf.merchandise.attribute',
        'variant_id',
        string='Attributes'
    )
    
    # Pricing
    price_extra = fields.Float(
        string='Price Extra',
        tracking=True,
        digits='Product Price',
        help='Additional price over base product price'
    )
    
    # Inventory
    stock_quantity = fields.Float(
        string='Stock Quantity',
        default=0,
        tracking=True
    )
    sku = fields.Char(
        string='SKU',
        tracking=True,
        help='Stock Keeping Unit'
    )
    
    # Media
    image = fields.Binary(
        string='Variant Image',
        tracking=True
    )
    
    # Status
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )
    total_price = fields.Float(
        compute='_compute_total_price',
        store=True,
        digits='Product Price'
    )

    @api.depends('product_id', 'name')
    def _compute_display_name(self):
        for variant in self:
            variant.display_name = f'{variant.product_id.name} - {variant.name}'

    @api.depends('product_id.list_price', 'price_extra')
    def _compute_total_price(self):
        for variant in self:
            variant.total_price = variant.product_id.list_price + variant.price_extra

    @api.constrains('sku')
    def _check_sku(self):
        for variant in self:
            if variant.sku:
                existing = self.search([
                    ('sku', '=', variant.sku),
                    ('id', '!=', variant.id)
                ])
                if existing:
                    raise ValidationError(_('SKU must be unique!'))


class VfMerchandiseAttribute(models.Model):
    _name = 'vf.merchandise.attribute'
    _description = 'Merchandise Attribute'
    _order = 'name'

    name = fields.Char(
        string='Attribute Name',
        required=True
    )
    value = fields.Char(
        string='Value',
        required=True
    )
    variant_id = fields.Many2one(
        'vf.merchandise.variant',
        string='Variant',
        required=True,
        ondelete='cascade'
    )
