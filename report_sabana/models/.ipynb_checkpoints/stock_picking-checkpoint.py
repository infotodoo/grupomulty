# -*- coding: utf-8 -*-
from odoo import models,fields,api,_
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    total_weigth = fields.Float('Total Weigth',compute="_compute_total_weigth")
    
    def update_action_assign(self):
        self.action_assign()
        for record in self.move_line_ids_without_package:
            record.qty_done = record.product_uom_qty
            
    @api.depends('move_ids_without_package.product_uom_qty','move_ids_without_package.weigth')
    def _compute_total_weigth(self):
        weigth = 0
        self.total_weigth = 0
        for record in self.move_ids_without_package:
            if record.weigth != 0 and record.product_uom_qty != 0:
                if record.weigth != 0:
                    weigth += record.weigth * record.product_uom_qty
                    self.write({'total_weigth':weigth})
        return weigth
                

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    weigth = fields.Float('Weigth',compute="_compute_weigth")
    
    @api.depends('product_id')
    def _compute_weigth(self):
        for record in self:
            record.weigth = 0
            if record.product_id:
                record.weigth = record.product_id.weight
                