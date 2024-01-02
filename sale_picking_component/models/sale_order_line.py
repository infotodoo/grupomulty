# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def _onchange_real_purchase_price(self):
        for item in self:
            if item.product_id.component_ids:
                total_cost=0
                for component in item.product_id.component_ids:
                    total_cost+=component.total
                item.real_purchase_price= total_cost