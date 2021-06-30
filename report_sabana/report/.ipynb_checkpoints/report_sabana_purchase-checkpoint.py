# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, tools, api,_
from datetime import datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

    
class ReportSabanaPurchase(models.Model):
    _name = 'report.sabana.purchase'
    _auto = False
    _description = 'This is the lines in the purchase sabana report'
    
    product_id = fields.Many2one('product.product','Product',readonly=True)
    name = fields.Many2one('account.move','Invoice',readonly=True)
    date_bill = fields.Date('Date',readonly=True)
    nit = fields.Char('Nit',readonly=True)
    partner_id_1 = fields.Many2one('res.partner','Vendor',readonly=True)
    partner_type_id_1 = fields.Many2one('res.partner.type','Vendor Type',readonly=True)
    invoice_user_id = fields.Many2one('res.users','Vendors',readonly=True)
    categ_id = fields.Many2one('product.category','Category',readonly=True)
    zone = fields.Many2one('res.partner.zone','Zone',readonly=True)
    quantity = fields.Float('Quantity',readonly=True)
    price_purchase = fields.Float('Purchase without tax',readonly=True)
    subtotal_purchase = fields.Float('Purchase with tax',compute="_compute_subtotal_purchase")
    discount = fields.Float('Discount %',readonly=True)
    weigth = fields.Float('Weigth',readonly=True)
    partner_deal_id_1 = fields.Many2one('res.partner.deal','Deal Name',compute="_compute_partner_deal_id_1")
    tax = fields.Float('Tax',compute="_compute_tax")
    type_credit = fields.Char('Invoice Type',readonly=True)
    
    @api.depends('partner_id_1')
    def _compute_partner_deal_id_1(self):
        for record in self:
            record.partner_deal_id_1 = None
            if record.partner_id_1:
                record.partner_deal_id_1 = record.partner_id_1.partner_deal_id
    
    @api.depends('price_purchase','tax')
    def _compute_subtotal_purchase(self):
        for record in self:
            if (record.price_purchase,record.tax) != 0:
                record.subtotal_purchase = record.price_purchase + record.tax
            elif record.price_purchase != 0:
                record.subtotal_purchase = record.price
            else:
                record.subtotal_purchase = 0
    
    @api.depends('price_purchase')
    def _compute_tax(self):
        iva_tax = 0
        rte_tax = 0
        for record in self:
            tax_ids = record.env['account.move.line'].search([('move_id','=',record.name.id),('product_id','=',record.product_id.id)])
            _logger.error('\n tax_ids')
            _logger.error(tax_ids.tax_ids.ids)
            record.tax = 0
            if tax_ids.tax_ids and record.price_purchase != 0:
                for taxes in tax_ids.tax_ids:
                    if taxes.amount > 0:
                        iva_tax += taxes.amount
                    elif taxes.amount < 0:
                        rte_tax += taxes.amount
                    else:
                        iva_tax = 0
                        rte_tax = 0
                record.tax = (record.price_purchase*(iva_tax/100))-(record.price_purchase*(rte_tax/100))
                
                
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_sabana_purchase')
        query = """
        CREATE or REPLACE VIEW report_sabana_purchase AS(
        
        select
        row_number() OVER (ORDER BY aml.id) as id,
        aml.product_id as product_id, aml.move_id as name,(case when am.type='in_invoice' then 'Factura de proveedor' when am.type='in_receipt' then 'Recibo de compra' end)as type_credit,am.invoice_date as date_bill,
        rp.identification_document as nit,am.partner_id as partner_id_1,
        rp.partner_type_id as partner_type_id_1,am.invoice_user_id as invoice_user_id,
        pt.categ_id as categ_id,rp.zone as zone, aml.quantity as quantity,
        (case when am.type='out_invoice' then aml.price_subtotal when am.type='out_refund' then aml.price_subtotal*(-1) end) as price_purchase,
        aml.weigth as weigth,aml.discount as discount
        from account_move_line aml
        left join account_move am on (am.id = aml.move_id) 
        left join res_partner rp on (rp.id = am.partner_id)
        left join product_product pp on (pp.id = aml.product_id)
        left join product_template pt on (pt.id = pp.product_tmpl_id)
        where product_id is not null and (am.type = 'in_invoice' or am.type = 'in_receipt') and am.state = 'posted'
        );
        """
        self.env.cr.execute(query)
