# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api,_

_logger = logging.getLogger(__name__)

    
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    total_weigth = fields.Float('Total Weigth')
    total_weigth_1 = fields.Float('Total Weigth',compute="_compute_total_weigth_1")
    pricelist = fields.Char('Pricelist')
    partner_deal_id = fields.Many2one('res.partner.deal',"Deal Name")
    partner_deal_id_1 = fields.Many2one('res.partner.deal',"Deal Name",compute="_compute_partner_deal_id_1")
    
    @api.depends('partner_id')
    def _compute_partner_deal_id_1(self):
        self.partner_deal_id_1 = None
        if self.partner_id:
            self.partner_deal_id_1 = self.partner_id.partner_deal_id
    
    @api.depends('invoice_line_ids.weigth')
    def _compute_total_weigth_1(self):
        weigth = 0
        self.total_weigth_1 = 0
        for record in self.invoice_line_ids:
            if record.product_id:
                if record.weigth != 0:
                    weigth += record.weigth 
                    self.write({'total_weigth_1':weigth})
                else:
                    self.total_weigth_1 = 0
            else:
                self.total_weigth_1 = 0
        return weigth
                
    @api.onchange('partner_id')
    def _onchange_partner_payment_mean_code_id(self):
        if self.partner_id:
            self.payment_mean_code_id = self.partner_id.payment_mean_code_id.id
    
    
class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    weigth = fields.Float('Weigth',store=True)
    
    @api.onchange('product_id','quantity')
    def _onchange_partner_id(self):
        for record in self:
            record.weigth = 0
            if record.product_id:
                record.weigth = record.product_id.weight * record.quantity
