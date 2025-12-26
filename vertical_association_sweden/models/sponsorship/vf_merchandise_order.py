# Copyright 2024 Vertikal Forening
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


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
    amount_total = fields.Float(
        compute='_compute_amounts',
        string='Total Amount',
        store=True,
        digits='Account'
    )
    amount_tax = fields.Float(
        compute='_compute_amounts',
        string='Tax',
        store=True,
        digits='Account'
    )
    amount_untaxed = fields.Float(
        compute='_compute_amounts',
        string='Untaxed Amount',
        store=True,
        digits='Account'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id
    )
    
    # Payment
    payment_state = fields.Selection([
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
    ], string='Payment Status', default='unpaid', tracking=True)
    payment_ids = fields.One2many(
        'account.payment',
        'merchandise_order_id',
        string='Payments'
    )
    
    # Shipping
    shipping_address_id = fields.Many2one(
        'res.partner',
        string='Shipping Address',
        tracking=True
    )
    tracking_number = fields.Char(
        string='Tracking Number',
        tracking=True
    )
    date_shipped = fields.Datetime(
        string='Date Shipped',
        readonly=True
    )
    
    # Order lines
    line_ids = fields.One2many(
        'vf.merchandise.order.line',
        'order_id',
        string='Order Lines'
    )
    
    # Notes
    notes = fields.Text(
        string='Order Notes',
        tracking=True
    )
    internal_notes = fields.Text(
        string='Internal Notes'
    )

    @api.depends('line_ids.price_total', 'line_ids.price_tax')
    def _compute_amounts(self):
        for order in self:
            amount_untaxed = sum(line.price_subtotal for line in order.line_ids)
            amount_tax = sum(line.price_tax for line in order.line_ids)
            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = amount_untaxed + amount_tax

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('order_number', _('New')) == _('New'):
                vals['order_number'] = self._generate_order_number()
        return super().create(vals_list)

    def _generate_order_number(self):
        """Generate a unique order number"""
        sequence = self.env['ir.sequence'].next_by_code('vf.merchandise.order') or '0000'
        return f'MO-{sequence}'

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Set shipping address to partner address by default"""
        if self.partner_id:
            self.shipping_address_id = self.partner_id.id
            # Check if partner is a member
            member = self.env['vf.member'].search([('partner_id', '=', self.partner_id.id)], limit=1)
            self.member_id = member.id if member else False

    def action_confirm(self):
        """Confirm the order"""
        self.write({'state': 'confirmed'})
        # Check stock availability
        self._check_stock_availability()
        return True

    def action_cancel(self):
        """Cancel the order"""
        self.write({'state': 'cancelled'})
        return True

    def action_ship(self):
        """Mark order as shipped"""
        self.write({
            'state': 'shipped',
            'date_shipped': fields.Datetime.now()
        })
        return True

    def action_deliver(self):
        """Mark order as delivered"""
        self.write({'state': 'delivered'})
        return True

    def _check_stock_availability(self):
        """Check if all items are in stock"""
        for line in self.line_ids:
            if line.product_id.track_inventory:
                if line.quantity > line.product_id.stock_quantity:
                    raise ValidationError(_(
                        'Insufficient stock for %s. Available: %s, Required: %s'
                    ) % (line.product_id.name, line.product_id.stock_quantity, line.quantity))

    def action_create_invoice(self):
        """Create invoice for this order"""
        self.ensure_one()
        if self.state not in ['confirmed', 'shipped']:
            raise ValidationError(_('Only confirmed orders can be invoiced.'))
        
        return {
            'name': _('Create Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_type': 'out_invoice',
                'default_partner_id': self.partner_id.id,
                'default_merchandise_order_id': self.id,
            },
        }

    def action_view_payments(self):
        """View payments for this order"""
        self.ensure_one()
        action = self.env.ref('account.action_account_payments').read()[0]
        action['domain'] = [('merchandise_order_id', '=', self.id)]
        return action


class VfMerchandiseOrderLine(models.Model):
    _name = 'vf.merchandise.order.line'
    _description = 'Merchandise Order Line'
    _order = 'order_id, sequence'

    order_id = fields.Many2one(
        'vf.merchandise.order',
        string='Order',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    # Product
    product_id = fields.Many2one(
        'vf.merchandise.product',
        string='Product',
        required=True
    )
    variant_id = fields.Many2one(
        'vf.merchandise.variant',
        string='Variant'
    )
    
    # Quantity and pricing
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
    discount = fields.Float(
        string='Discount (%)',
        default=0
    )
    
    # Computed fields
    price_subtotal = fields.Float(
        compute='_compute_price',
        string='Subtotal',
        store=True,
        digits='Account'
    )
    price_tax = fields.Float(
        compute='_compute_price',
        string='Tax',
        store=True,
        digits='Account'
    )
    price_total = fields.Float(
        compute='_compute_price',
        string='Total',
        store=True,
        digits='Account'
    )
    
    # Description
    name = fields.Text(
        string='Description'
    )

    @api.depends('quantity', 'unit_price', 'discount')
    def _compute_price(self):
        for line in self:
            subtotal = line.quantity * line.unit_price
            discount_amount = subtotal * (line.discount / 100)
            line.price_subtotal = subtotal - discount_amount
            # Simple tax calculation - in practice, use proper tax rules
            line.price_tax = line.price_subtotal * 0.25  # 25% tax
            line.price_total = line.price_subtotal + line.price_tax

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set default values from product"""
        if self.product_id:
            self.unit_price = self.product_id.list_price
            self.name = self.product_id.description or self.product_id.name

    @api.onchange('variant_id')
    def _onchange_variant_id(self):
        """Update price based on variant"""
        if self.variant_id:
            self.unit_price = self.variant_id.total_price
