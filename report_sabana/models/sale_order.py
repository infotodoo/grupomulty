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

    @api.model
    def create(self, vals):
        if not 'discount' in vals.get('order_line')[0][2]:
            product_obj = self.env['product.product'].browse(vals.get('order_line')[0][2].get('product_id'))
            partner_obj = self.env['res.partner'].browse(vals.get('partner_id'))
            
            if 'pricelist_id' not in vals:
                pricelist_id = self.env['product.pricelist'].browse(partner_obj.property_product_pricelist and partner_obj.property_product_pricelist.id or 0)
            else:
                pricelist_id = self.env['product.pricelist'].browse(vals.get('pricelist_id'))
                
            product_uom = self.env['uom.uom'].browse(vals.get('order_line')[0][2].get('product_uom'))
            product_uom_qty = vals.get('order_line')[0][2].get('product_uom_qty')
            date_order = vals.get('date_order')
            
            if not product_obj:
                raise ValidationError('No existe producto definido')
            
            product = product_obj.with_context(
                lang=partner_obj.lang,
                partner=partner_obj,
                quantity=product_uom_qty,
                date=date_order,
                pricelist=pricelist_id.id,
                uom=product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            product_context = dict(self.env.context, partner_id=partner_obj.id, date=date_order, uom=product_uom.id)
            price, rule_id = pricelist_id.with_context(product_context).get_product_price_rule(product_obj, product_uom_qty or 1.0, partner_obj)
            new_sale_order = self.env['sale.order.line']
            new_list_price, currency = new_sale_order.with_context(product_context)._get_real_price_currency(product, rule_id, product_uom_qty, product_uom, pricelist_id.id)
            discount = (new_list_price - price) / new_list_price * 100
            vals['order_line'][0][2].update({
                'discount': float(discount),
            })

        res = super(SaleOrder, self).create(vals)
        return res


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
