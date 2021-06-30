# -*- coding: utf-8 -*-
# LUIS FELIPE PATERNINA VITAL
#Todoo SAS


from odoo import models, fields


class RespartnerDeal(models.Model):

    _name = "res.partner.deal"
    _description = "res partner deal"
    
    name = fields.Char('Name', required=True)
    

class RespartnerMulti(models.Model):

    _inherit = "res.partner"
    
    zone = fields.Many2one('res.partner.zone', string="Zona")
    partner_type_id = fields.Many2one('res.partner.type', string="Tipo de Cliente")
    partner_deal_id = fields.Many2one('res.partner.deal', string="Deal Name")






    
    
    