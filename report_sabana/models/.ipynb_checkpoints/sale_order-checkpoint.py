# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api,_

_logger = logging.getLogger(__name__)

    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    total_weigth = fields.Float('Total Weigth',compute="_compute_total_weigth",store=True)
    partner_deal_id = fields.Many2one('res.partner.deal',"Deal Name",related="partner_id.partner_deal_id")
    partner_payment_mean_code_id = fields.Many2one('account.payment.mean.code',"Deal Name",related="partner_id.payment_mean_code_id")
    bool_manager = fields.Boolean('bool',compute='_validate_user_group1')
    
    def _validate_user_group1(self):
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self.bool_manager = True
        else:
            self.bool_manager = False

    @api.depends('order_line.weigth')
    def _compute_total_weigth(self):
        weigth = 0
        for record in self.order_line:
            if record.product_id:
                if record.weigth != 0:
                    weigth += record.weigth
                    self.write({'total_weigth':weigth})
                else:
                    self.total_weigth = 0
            else:
                self.total_weigth = 0
        return weigth
                
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals.update({'total_weigth': self.total_weigth,
                             'pricelist':self.pricelist_id.name,
                             'partner_deal_id':self.partner_deal_id.id})
        return invoice_vals


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    weigth = fields.Float('Weigth',store=True)
    bool_manager = fields.Boolean('bool',compute='_validate_user_group')
    
    @api.onchange('product_id','product_uom_qty')
    def _onchange_partner_id(self):
        for record in self:
            record.weigth = 0
            if record.product_id:
                record.weigth = record.product_id.weight * record.product_uom_qty
    
    def _prepare_invoice_line(self):
        res = super(SaleOrderLine, self)._prepare_invoice_line()
        res.update({'weigth': self.weigth})
        return res
    
    def _validate_user_group(self):
        if self.env.user.has_group('sales_team.group_sale_manager'):
            self.bool_manager = True
        else:
            self.bool_manager = False
            

class PosOrder(models.Model):
    _inherit = "pos.order"
    
    def _prepare_invoice_line(self,order_line):
        res = super(PosOrder, self)._prepare_invoice_line(order_line)
        res.update({'weigth': order_line.product_id.weight})
        return res
    
    def _prepare_invoice_vals(self):
        weight = 0
        for record in self.lines:
            weight += record.product_id.weight * record.qty
        vals = super(PosOrder, self)._prepare_invoice_vals()
        vals.update({'total_weigth':weight,
                     'partner_deal_id':self.partner_id.partner_deal_id.id,
                     'pricelist':self.pricelist_id.name
                    })
        return vals