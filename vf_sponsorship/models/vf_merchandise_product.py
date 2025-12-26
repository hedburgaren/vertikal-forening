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
    
    # Categorization
    category_id = fields.Many2one(
        'vf.merchandise.category',
        string='Category',
        required=True,
        tracking=True
    )
    
    # Product template link
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Product Template',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    # Merchandise specific
    is_limited_edition = fields.Boolean(
        string='Limited Edition',
        default=False,
        tracking=True
    )
    edition_number = fields.Integer(
        string='Edition Number',
        help='Number for limited edition items'
    )
    max_quantity = fields.Integer(
        string='Maximum Quantity',
        help='Maximum quantity that can be produced/sold'
    )
    
    # Visibility
    show_on_website = fields.Boolean(
        string='Show on Website',
        default=True
    )
    show_to_members_only = fields.Boolean(
        string='Members Only',
        default=False,
        help='Only visible to logged-in members'
    )
    
    # Pricing
    member_price = fields.Float(
        string='Member Price',
        digits='Product Price',
        help='Special price for association members'
    )
    non_member_price = fields.Float(
        string='Non-Member Price',
        digits='Product Price',
        help='Price for non-members'
    )
    
    # Sizing and variants
    has_sizes = fields.Boolean(
        string='Has Sizes',
        default=False
    )
    size_ids = fields.Many2many(
        'product.attribute.value',
        string='Available Sizes',
        domain="[('attribute_id.name', '=', 'Size')]"
    )
    has_colors = fields.Boolean(
        string='Has Colors',
        default=False
    )
    color_ids = fields.Many2many(
        'product.attribute.value',
        string='Available Colors',
        domain="[('attribute_id.name', '=', 'Color')]"
    )
    
    # Images
    image_ids = fields.Many2many(
        'ir.attachment',
        'vf_merchandise_product_image_rel',
        'product_id',
        'image_id',
        string='Product Images'
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('sold_out', 'Sold Out'),
        ('discontinued', 'Discontinued'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Statistics
    total_sold = fields.Integer(
        compute='_compute_statistics',
        string='Total Sold'
    )
    total_revenue = fields.Float(
        compute='_compute_statistics',
        string='Total Revenue',
        digits='Account'
    )
    stock_available = fields.Float(
        compute='_compute_stock',
        string='Stock Available'
    )
    
    # Computed fields
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('name', 'category_id')
    def _compute_display_name(self):
        for product in self:
            if product.category_id:
                product.display_name = f'{product.category_id.name} / {product.name}'
            else:
                product.display_name = product.name

    @api.depends('product_tmpl_id')
    def _compute_statistics(self):
        for product in self:
            # Get all sales orders for this product
            orders = self.env['sale.order.line'].search([
                ('product_template_id', '=', product.product_tmpl_id.id),
                ('order_id.state', 'in', ['sale', 'done'])
            ])
            product.total_sold = int(sum(orders.mapped('product_uom_qty')))
            product.total_revenue = sum(orders.mapped('price_total'))

    @api.depends('product_tmpl_id')
    def _compute_stock(self):
        for product in self:
            # Get stock from product template
            product.stock_available = product.product_tmpl_id.qty_available

    @api.onchange('has_sizes')
    def _onchange_has_sizes(self):
        """Add size attribute when enabled"""
        if self.has_sizes and self.product_tmpl_id:
            # Ensure size attribute exists
            size_attr = self.env['product.attribute'].search([('name', '=', 'Size')], limit=1)
            if not size_attr:
                size_attr = self.env['product.attribute'].create({'name': 'Size'})
            
            # Add to product template
            if size_attr not in self.product_tmpl_id.attribute_line_ids.mapped('attribute_id'):
                self.env['product.template.attribute.line'].create({
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'attribute_id': size_attr.id,
                    'value_ids': [(6, 0, self.size_ids.ids)],
                })

    @api.onchange('has_colors')
    def _onchange_has_colors(self):
        """Add color attribute when enabled"""
        if self.has_colors and self.product_tmpl_id:
            # Ensure color attribute exists
            color_attr = self.env['product.attribute'].search([('name', '=', 'Color')], limit=1)
            if not color_attr:
                color_attr = self.env['product.attribute'].create({'name': 'Color'})
            
            # Add to product template
            if color_attr not in self.product_tmpl_id.attribute_line_ids.mapped('attribute_id'):
                self.env['product.template.attribute.line'].create({
                    'product_tmpl_id': self.product_tmpl_id.id,
                    'attribute_id': color_attr.id,
                    'value_ids': [(6, 0, self.color_ids.ids)],
                })

    def action_make_available(self):
        """Make product available for sale"""
        self.ensure_one()
        if not self.product_tmpl_id.sale_ok:
            self.product_tmpl_id.sale_ok = True
        self.state = 'available'
        return True

    def action_mark_sold_out(self):
        """Mark product as sold out"""
        self.ensure_one()
        self.state = 'sold_out'
        self.product_tmpl_id.sale_ok = False
        return True

    def action_discontinue(self):
        """Discontinue the product"""
        self.ensure_one()
        self.state = 'discontinued'
        self.product_tmpl_id.active = False
        return True

    def action_view_sales(self):
        """View sales for this product"""
        self.ensure_one()
        
        action = self.env.ref('sale.action_order_line_product_tree').read()[0]
        action['domain'] = [('product_template_id', '=', self.product_tmpl_id.id)]
        return action

    def action_create_sale_order(self):
        """Create a sale order for this product"""
        self.ensure_one()
        
        return {
            'name': _('Create Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_order_line': [(0, 0, {
                    'product_template_id': self.product_tmpl_id.id,
                    'product_id': self.product_tmpl_id.product_variant_ids[0].id if self.product_tmpl_id.product_variant_ids else False,
                    'price_unit': self.member_price if self.env.user.has_group('vf_base.vf_user') else self.non_member_price,
                })],
            },
        }

    @api.model
    def create(self, vals):
        """Override to create product template if not provided"""
        if not vals.get('product_tmpl_id'):
            # Create product template
            template_vals = {
                'name': vals.get('name'),
                'sale_ok': False,  # Will be enabled when made available
                'purchase_ok': False,
                'type': 'product',
                'detailed_type': 'product',
            }
            template = self.env['product.template'].create(template_vals)
            vals['product_tmpl_id'] = template.id
        
        return super().create(vals)
