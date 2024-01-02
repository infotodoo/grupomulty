# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    component_ids = fields.One2many('product.component','product_id','Componentes',copy=True)
    
class ProductComponent(models.Model):
    _name = 'product.component'
    _rec_name = 'product_component_id'

    product_id = fields.Many2one('product.product',string='Producto',copy=True)
    product_component_id = fields.Many2one('product.product',string='Producto',copy=True)
    product_qty = fields.Float(string='Cantidad',copy=True)
    product_uom = fields.Many2one('uom.uom',string='Unidad de Medida',copy=True)
    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda x: x.env.company.currency_id)
    cost = fields.Monetary(currency_field='currency_id', string='Costo')
    total = fields.Monetary(currency_field='currency_id', string='Total')
    partner_id = fields.Many2one('res.partner', string='Proveedor',copy=True)
    note = fields.Text()
    
    @api.onchange("cost","product_qty")
    def _onchange_total(self):
        self.total = self.cost * self.product_qty
        
    @api.onchange('product_component_id','product_id')
    def _custom_onchange_product_id(self):
        for item in self:
            if item.product_component_id and item.product_component_id.uom_id:
                item.product_uom = item.product_component_id.uom_id
            elif item.product_id and item.product_id.uom_id:
                item.product_uom = item.product_id.uom_id