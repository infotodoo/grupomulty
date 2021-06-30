# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api,_
from odoo.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)

    
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    total_weigth = fields.Float('Total Weigth',compute="_compute_total_weigth",store=True)
    partner_deal_id = fields.Many2one('res.partner.deal',"Deal Name",related="partner_id.partner_deal_id")

    @api.depends('order_line.weigth')
    def _compute_total_weigth(self):
        weigth = 0
        for record in self.order_line:
            if record.product_id:
                if record.weigth != 0:
                    weigth += record.weigth * record.product_uom_qty
                    self.write({'total_weigth':weigth})
                else:
                    self.total_weigth = 0
            else:
                self.total_weigth = 0
        #return weight


                
class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    weigth = fields.Float('Weigth',store=True)
    
    @api.onchange('product_id','product_uom_qty')
    def _onchange_partner_id(self):
        for record in self:
            record.weigth = 0
            if record.product_id:
                record.weigth = record.product_id.weight * record.product_uom_qty
                
    
    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine,self)._prepare_account_move_line(move)
        res['weigth'] = self.weigth
        return res
