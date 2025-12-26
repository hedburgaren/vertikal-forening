# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class VfMerchandiseOrder(models.Model):
    _name = 'vf.merchandise.order'
    _description = 'Merchandise Order'
    _order = 'date_ordered desc'
    _rec_name = 'order_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    order_number = fields.Char(
        string='Order Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    
    # Customer
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    member_id = fields.Many2one(
        'vf.member',
        string='Member',
        tracking=True,
        help='If customer is a member'
    )
    
    # Order details
    date_ordered = fields.Datetime(
        string='Order Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Financial
    total_amount = fields.Float(
        compute='_compute_totals',
        string='Total Amount',
        digits='Account',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    # Payment
    payment_status = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ], compute='_compute_payment_status', string='Payment Status')
    
    # Shipping
    shipping_address_id = fields.Many2one(
        'res.partner',
        string='Shipping Address'
    )
    tracking_number = fields.Char(
        string='Tracking Number'
    )
    shipping_date = fields.Datetime(
        string='Shipping Date'
    )
    
    # Notes
    order_notes = fields.Text(
        string='Order Notes'
    )
    internal_notes = fields.Text(
        string='Internal Notes'
    )
    
    # Relations
    line_ids = fields.One2many(
        'vf.merchandise.order.line',
        'order_id',
        string='Order Lines'
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sales Order',
        readonly=True
    )
    
    _sql_constraints = [
        ('order_number_unique', 'unique(order_number)', 
         'Order number must be unique!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('order_number', _('New')) == _('New'):
                vals['order_number'] = self._generate_order_number()
        return super().create(vals_list)

    def _generate_order_number(self):
        """Generate unique order number"""
        sequence = self.env['ir.sequence'].next_by_code('vf.merchandise.order') or '00001'
        return f'MO-{sequence}'

    @api.depends('line_ids.price_total')
    def _compute_totals(self):
        for order in self:
            order.total_amount = sum(order.line_ids.mapped('price_total'))

    @api.depends('sale_order_id.amount_total', 'sale_order_id.amount_paid')
    def _compute_payment_status(self):
        for order in self:
            if not order.sale_order_id:
                order.payment_status = 'unpaid'
            else:
                if order.sale_order_id.amount_paid >= order.sale_order_id.amount_total:
                    order.payment_status = 'paid'
                elif order.sale_order_id.amount_paid > 0:
                    order.payment_status = 'partial'
                else:
                    order.payment_status = 'unpaid'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Set member if partner is a member"""
        if self.partner_id:
            member = self.env['vf.member'].search([('partner_id', '=', self.partner_id.id)], limit=1)
            self.member_id = member.id if member else False
            self.shipping_address_id = self.partner_id.id

    def action_confirm(self):
        """Confirm the order and create sales order"""
        self.ensure_one()
        
        if not self.line_ids:
            raise ValidationError(_('Please add at least one product to the order.'))
        
        # Create sales order
        sale_order_vals = {
            'partner_id': self.partner_id.id,
            'partner_shipping_id': self.shipping_address_id.id or self.partner_id.id,
            'date_order': self.date_ordered,
            'state': 'draft',
            'order_line': [],
            'note': self.order_notes,
        }
        
        # Add order lines
        for line in self.line_ids:
            sale_order_vals['order_line'].append((0, 0, {
                'product_template_id': line.product_id.product_tmpl_id.id,
                'product_id': line.product_id.product_tmpl_id.product_variant_ids[0].id,
                'product_uom_qty': line.quantity,
                'price_unit': line.unit_price,
                'name': line.product_id.name,
            }))
        
        sale_order = self.env['sale.order'].create(sale_order_vals)
        self.sale_order_id = sale_order.id
        self.state = 'confirmed'
        
        # Confirm sales order
        sale_order.action_confirm()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        """Cancel the order"""
        self.ensure_one()
        
        if self.sale_order_id and self.sale_order_id.state not in ['cancel', 'done']:
            self.sale_order_id.action_cancel()
        
        self.state = 'cancelled'
        return True

    def action_mark_shipped(self):
        """Mark order as shipped"""
        self.ensure_one()
        self.state = 'shipped'
        self.shipping_date = fields.Datetime.now()
        
        # Send shipping confirmation email
        if self.partner_id.email:
            template = self.env.ref('vf_sponsorship.email_template_shipping_confirmation')
            template.send_mail(self.id)
        
        return True

    def action_mark_delivered(self):
        """Mark order as delivered"""
        self.ensure_one()
        self.state = 'delivered'
        
        # Send delivery confirmation email
        if self.partner_id.email:
            template = self.env.ref('vf_sponsorship.email_template_delivery_confirmation')
            template.send_mail(self.id)
        
        return True

    def action_view_sale_order(self):
        """View the associated sales order"""
        self.ensure_one()
        
        if not self.sale_order_id:
            raise ValidationError(_('No sales order created yet.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class VfMerchandiseOrderLine(models.Model):
    _name = 'vf.merchandise.order.line'
    _description = 'Merchandise Order Line'
    _order = 'order_id, id'

    # Relations
    order_id = fields.Many2one(
        'vf.merchandise.order',
        string='Order',
        required=True,
        ondelete='cascade'
    )
    product_id = fields.Many2one(
        'vf.merchandise.product',
        string='Product',
        required=True
    )
    
    # Product details
    name = fields.Char(
        string='Description',
        required=True
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1
    )
    unit_price = fields.Float(
        string='Unit Price',
        required=True,
        digits='Product Price'
    )
    
    # Variants
    size_id = fields.Many2one(
        'product.attribute.value',
        string='Size',
        domain="[('attribute_id.name', '=', 'Size')]"
    )
    color_id = fields.Many2one(
        'product.attribute.value',
        string='Color',
        domain="[('attribute_id.name', '=', 'Color')]"
    )
    
    # Computed
    price_total = fields.Float(
        compute='_compute_price_total',
        string='Total',
        digits='Account',
        store=True
    )
    
    @api.depends('quantity', 'unit_price')
    def _compute_price_total(self):
        for line in self:
            line.price_total = line.quantity * line.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update price and description based on product"""
        if self.product_id:
            self.name = self.product_id.name
            # Use member price if applicable
            if self.order_id.member_id and self.product_id.member_price:
                self.unit_price = self.product_id.member_price
            elif self.product_id.non_member_price:
                self.unit_price = self.product_id.non_member_price
            else:
                # Get price from product template
                if self.product_id.product_tmpl_id.list_price:
                    self.unit_price = self.product_id.product_tmpl_id.list_price
