from odoo import models, fields, api, _
import logging

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_esp_id = fields.Many2one(
        'hr.employee',
        string="Especialista",
        tracking=True)
    purchase_id = fields.Many2one(
        'purchase.order',
        string="Orden de Compra",
        tracking=True)
    purchaseorder = fields.Char(
        string="Orden de compra",
        store="True",
        tracking=True)
    adional_costs_ids = fields.One2many(
        'sale.order.aditional.costs',
        'sale_order_id',
        string="Costos adicionales",
        tracking=True)
    cost_total = fields.Float(
        string="Costos adicionales",
        store="True",
        tracking=True)
    margin = fields.Monetary(
        "Margin",
        compute='_compute_margin',
        store=True,
        tracking=True)
    margin_percent = fields.Float(
        "Margin (%)",
        compute='_compute_margin',
        store=True,
        tracking=True)
    margin_percent_real = fields.Float(
        "Margen %",
        store=True,
        compute="_compute_margin_real")
    margin_real = fields.Float(
        "Utilidad",
        store=True,
        compute="_compute_margin_real")


    @api.depends('order_line.margin_real', 'amount_untaxed','adional_costs_ids')
    def _compute_margin_real(self):
        if not all(self._ids):
            for order in self:
                order.margin_real = sum(order.order_line.mapped('margin_real_total')) - order.cost_total
                order.margin_percent_real = order.amount_untaxed and order.margin_real/order.amount_untaxed
        else:
            for order in self:
                order.margin_real = sum(order.order_line.mapped('margin_real_total')) - order.cost_total
                order.margin_percent_real = order.amount_untaxed and order.margin_real/order.amount_untaxed

    @api.onchange('adional_costs_ids')
    def _calculated_total_cost(self):
        sum = 0
        for line in self.adional_costs_ids:
            sum = line.cost + sum
        
        self.cost_total = sum

    @api.onchange('adional_costs_ids', 'order_line')
    def calculated_new_total_cost(self):
        for record in self:
            if record.adional_costs_ids:
                record.margin = record.margin - record.cost_total
            else:
                print("No hay costos adicionales")



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    vendors_id = fields.Many2one(
        'res.partner',
        string="Proveedor",
        tracking=True)
    cost_total = fields.Float(
        string="Total")
    real_purchase_price = fields.Float(
        string="Costo real unitario",
        tracking=True)
    margin_percent_real = fields.Float(
        "Margen real unitario",
        compute="_compute_margin_percent_real",
        store=True)
    margin_real = fields.Float(
        "Utilidad",
        store=True,
        compute="_compute_margin_real")
    margin_real_total = fields.Float(
        "Utilidad total",
        store=True,
        compute="_compute_margin_real_total")


    @api.onchange('product_id')
    def calculated_total_cost_lines(self):
        if self.product_id:
            self.real_purchase_price = self.real_purchase_price + self.cost_total
        else:
            self.real_purchase_price = 0.0

    @api.depends('real_purchase_price','product_uom_qty','price_unit')
    def _compute_margin_real(self):
        for line_margin in self:
            if line_margin.real_purchase_price:
                line_margin.margin_real = line_margin.price_unit - line_margin.real_purchase_price
            else:
                line_margin.margin_real = line_margin.price_unit - line_margin.real_purchase_price

    @api.depends('real_purchase_price','product_uom_qty','price_unit')
    def _compute_margin_real_total(self):
        for line_margin in self:
            if line_margin.real_purchase_price:
                line_margin.margin_real_total = (line_margin.price_unit - line_margin.real_purchase_price) * line_margin.product_uom_qty
            else:
                line_margin.margin_real_total = (line_margin.price_unit - line_margin.real_purchase_price) * line_margin.product_uom_qty

    @api.depends('margin_real')
    def _compute_margin_percent_real(self):
        for line_margin in self:
            if line_margin.margin_real and line_margin.price_unit > 0:
                line_margin.margin_percent_real = line_margin.margin_real / line_margin.price_unit
            else:
                line_margin.margin_percent_real = 0
