# -*- coding: utf-8 -*-
# LUIS FELIPE PATERNINA VITAL
#Todoo SAS


from odoo import models, fields

class RespartnerMulti(models.Model):

    _inherit = "res.partner"
    zone = fields.Many2one('res.partner.zone', string="Zona")
    partner_type_id = fields.Many2one('res.partner.type', string="Tipo de Cliente")
   

 
   







    
    
    