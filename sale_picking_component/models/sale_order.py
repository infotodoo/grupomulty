# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    def action_confirm(self, group_id=False):
        res = super(SaleOrder, self).action_confirm()
        picking_id = self.env['stock.picking'].search([('sale_id', '=', self.id)], order="id desc", limit=1)
        for line in self.order_line:
            if line.product_id.component_ids:
                for component in line.product_id.component_ids:
                    if component.product_component_id.type != 'service':
                        picking_id.move_ids_without_package =  [(0, 0, {
                            'name': component.product_component_id.name,
                            'product_id': component.product_component_id.id,
                            'product_uom_qty': line.product_uom_qty * component.product_qty,
                            'product_uom': component.product_uom.id,
                            'price_unit': component.cost,
                            'picking_id': picking_id.id,
                            'sale_line_id': line.id,
                            'location_id':picking_id.location_id.id,
                            'location_dest_id':picking_id.location_dest_id.id,
                        })]
        return res
