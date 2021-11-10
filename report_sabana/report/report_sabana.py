# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, tools, api,_
from datetime import datetime
from odoo.osv import expression
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

    
class ReportSabana(models.Model):
    _name = 'report.sabana'
    _auto = False
    _description = 'This is the lines in the sabana report'
    
    product_id = fields.Many2one('product.product','Product',readonly=True)
    name = fields.Many2one('account.move','Invoice',readonly=True)
    name_invoice = fields.Char('Factura',readonly=True)
    #name_pos = fields.Many2one('pos.order','Pos Ref',readonly=True)
    date_bill = fields.Date('Date',readonly=True)
    nit = fields.Char('Nit',readonly=True)
    partner_id = fields.Many2one('res.partner','Customer',readonly=True)
    partner_type_id = fields.Many2one('res.partner.type','Customer Type',readonly=True)
    invoice_user_id = fields.Many2one('res.users','Vendors',readonly=True)
    categ_id = fields.Many2one('product.category','Category',readonly=True)
    zone = fields.Many2one('res.partner.zone','Zone',readonly=True)
    quantity = fields.Float('Quantity',readonly=True)
    price = fields.Float('Sale with tax',readonly=True)#
    subtotal = fields.Float('Sale without tax',compute="_compute_subtotal")
    discount = fields.Float('Discount %',readonly=True)
    weigth = fields.Float('Weigth',readonly=True)
    pricelist = fields.Char('Pricelist',readonly=True)
    partner_deal_id = fields.Many2one('res.partner.deal','Deal Name',readonly=True)
    tax = fields.Float('Tax',compute="_compute_tax")
    team_id = fields.Many2one('crm.team','Sold Channel',readonly=True)
    type_credit = fields.Char('Invoice Type',readonly=True)
    
    
    @api.depends('price','tax')
    def _compute_subtotal(self):
        for record in self:
            if (record.price,record.tax) != 0:
                if record.type_credit != 'out_refund':
                    record.subtotal = record.price + record.tax
                else:
                    record.subtotal = (record.price + record.tax) * (-1)
            elif record.price != 0:
                if record.type_credit != 'out_refund':
                    record.subtotal = record.price
                else:
                    record.subtotal = record.price * (-1)
            else:
                record.subtotal = 0
    
    @api.depends('price')
    def _compute_tax(self):
        iva_tax = 0
        rte_tax = 0
        for record in self:
            tax_ids = record.env['account.move.line'].search([('move_id','=',record.name.id),('product_id','=',record.product_id.id)])
            _logger.error('\n tax_ids')
            _logger.error(tax_ids.tax_ids.ids)
            record.tax = 0
            if tax_ids.tax_ids and record.price != 0:
                for taxes in tax_ids.tax_ids:
                    if taxes.amount > 0:
                        iva_tax += taxes.amount
                    elif taxes.amount < 0:
                        rte_tax += taxes.amount
                    else:
                        iva_tax = 0
                        rte_tax = 0
                record.tax = (record.price*(iva_tax/100))-(record.price*(rte_tax/100))
                
                
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'report_sabana')
        query = """
        CREATE or REPLACE VIEW report_sabana AS(
        
        select
            row_number() OVER (ORDER BY sabana.id) as id,
            sabana.product_id as product_id, 
            sabana.name as name,
            sabana.name_invoice as name_invoice,
            sabana.type_credit as type_credit,
            sabana.date_bill as date_bill,
            sabana.nit as nit,
            sabana.partner_id as partner_id,
            sabana.partner_type_id as partner_type_id,
            sabana.invoice_user_id as invoice_user_id,
            sabana.categ_id as categ_id,
            sabana.zone as zone, 
            sabana.quantity as quantity,
            sabana.price as price,
            sabana.weigth as weigth,
            sabana.discount as discount,
            sabana.pricelist as pricelist,
            sabana.partner_deal_id as partner_deal_id,
            sabana.team_id as team_id
            
            
            from (
        
                select
                --row_number() OVER (ORDER BY aml.id) as id,
                aml.id as id,
                aml.product_id as product_id, 
                am.name as name_invoice,
                aml.move_id as name,
                (case when am.type='out_invoice' then 'Factura de cliente' when am.type='out_refund' then 'Recibo de ventas' end)as type_credit,
                am.invoice_date as date_bill,
                rp.identification_document as nit,
                am.partner_id as partner_id,
                rp.partner_type_id as partner_type_id,
                am.invoice_user_id as invoice_user_id,
                pt.categ_id as categ_id,
                rp.zone as zone, 
                aml.quantity as quantity,
                (case when am.type='out_invoice' then aml.price_subtotal when am.type='out_refund' then aml.price_subtotal*(-1) end) as price,
                aml.weigth as weigth,aml.discount as discount,
                am.pricelist as pricelist,
                am.partner_deal_id as partner_deal_id,am.team_id as team_id
                from account_move_line aml
                left join account_move am on (am.id = aml.move_id) 
                left join res_partner rp on (rp.id = am.partner_id)
                left join product_product pp on (pp.id = aml.product_id)
                left join product_template pt on (pt.id = pp.product_tmpl_id)
                where product_id is not null and (am.type = 'out_invoice' or am.type = 'out_refund') and am.state = 'posted'

                UNION ALL


                select
                --row_number() OVER (ORDER BY pol.id) as id,
                pol.id as id,
                pol.product_id as product_id, 
                po.name as name_invoice,
                0::integer as name,
                'Factura de punto de venta'::text as type_credit,
                po.date_order as date_bill,
                rp.identification_document as nit,
                po.partner_id as partner_id,
                rp.partner_type_id as partner_type_id,
                po.user_id as invoice_user_id,
                pt.categ_id as categ_id,
                rp.zone as zone, 
                pol.qty as quantity,
                pol.price_subtotal_incl as price,
                pp.weight * pol.qty as weigth,
                pol.discount as discount,
                pl.name as pricelist,
                rp.partner_deal_id as partner_deal_id,
                0::integer as team_id


                from pos_order_line pol

                left join pos_order po on (po.id = pol.order_id)
                left join res_partner rp on (rp.id = po.partner_id)
                left join product_product pp on (pp.id = pol.product_id)
                left join product_template pt on (pt.id = pp.product_tmpl_id)
                left join product_pricelist pl on (pl.id = po.pricelist_id)
                where pol.product_id is not null and po.state in ('done')
            ) as sabana
        );
        """
        self.env.cr.execute(query)