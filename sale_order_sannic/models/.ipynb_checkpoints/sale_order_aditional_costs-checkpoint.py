from odoo import models, fields, api

class SaleOrderAdionalCosts(models.Model):
    _name = 'sale.order.aditional.costs'
    _description = 'Aditional costs'

    name =  fields.Char(string="Nombre del costo adicional", tracking=True)
    cost = fields.Float(string="Valor del costo", tracking=True)
    sale_order_id = fields.Many2one('sale.order', string="Orden de venta")
    cost_total = fields.Float(string="Total", tracking=True)
    freigth_id = fields.Many2one('sale.order.aditional.freight',string="Nombre del costo adicional", tracking=True)
