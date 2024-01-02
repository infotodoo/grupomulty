# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    purchase_id = fields.Many2one(
        'purchase.order',
        'Orden de Compra',
        copy=True)
    custom_vendor_id = fields.Many2one(
        'res.partner',
        'Vendor',
        copy=True)
    custom_vendor_ids = fields.Many2many(
        'res.partner',
        string='Vendors',
        copy=False, )
    component_ids = fields.One2many(
        related='product_id.component_ids',
        readonly=True)
    vendor_active = fields.Boolean(string='Compra?')

    def _prepare_procurement_values(self, group_id=False):
        res = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        if self.custom_vendor_id:
            res.update({
                'supplier_id': self.custom_vendor_id,
            })
        return res

    @api.onchange('product_id')
    def _custom_onchange_product_id(self):
        seller_ids = self.product_id.seller_ids.partner_id
        self.custom_vendor_ids = seller_ids.ids
        return {'domain': {'custom_vendor_id': [('supplier_rank', '>', 0)]}}

    @api.onchange('custom_vendor_id')
    def _onchange_custom_vendor_id(self):
        res = {}
        if self.custom_vendor_id:
            supplier = self.product_id._select_seller(
                partner_id=self.custom_vendor_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order or fields.Datetime.now(),
                uom_id=self.product_uom or self.product_id.uom_id,
            )
            if not supplier:
                supplier = self.custom_vendor_id
            else:
                order_id = self.order_id
                frm_cur = self.env.company.currency_id
                to_cur = order_id.pricelist_id.currency_id
                purchase_price = supplier.price
                if frm_cur != to_cur:
                    purchase_price = frm_cur._convert(
                        purchase_price, to_cur, order_id.company_id or self.env.company,
                                                order_id.date_order or fields.Date.today(), round=False)
                self.purchase_price = purchase_price
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    sale_description = fields.Text(
        string="Descripción",
        tracking=True)

    def action_confirm(self, group_id=False):
        res = super(SaleOrder, self).action_confirm()
        
        
        line_dict = {}
        for line in self.order_line:
            if line.vendor_active:
                vendor_id = line.custom_vendor_id.id
                if vendor_id in line_dict:
                    line_dict[vendor_id].append(line)
                else:
                    line_dict[vendor_id] = [line]
        
        
        # Recorrer el diccionario y crear un purchase_id para cada grupo de líneas        
        if len(line_dict) > 0:
            for vendor_id, vendor_lines in line_dict.items():
                order_lines = []
                for line in vendor_lines:
                    order_line = (0, 0, {
                        'name': line.name,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'price_unit': line.real_purchase_price,
                        'date_planned': self.date_order,
                        'sale_line_id': line.id
                    })
                    order_lines.append(order_line)
            
                # Crear el registro de compra para el vendor_id actual
                purchase_id = self.env['purchase.order'].create({
                    'saleorder_id': self.id,
                    'partner_id': vendor_id,
                    'currency_id': self.currency_id.id,
                    'order_line': order_lines,
                    'date_order': self.date_order,
                })
            

        return res
