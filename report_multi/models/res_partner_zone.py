# -*- coding: utf-8 -*-
# LUIS FELIPE PATERNINA VITAL
#Todoo SAS


from odoo import models, fields

class RespartnerMulti(models.Model):

    _name = "res.partner.zone"
    name = fields.Char(string='Nombre', required=True)
    res_city_id = fields.Many2one('res.city', string="Ciudad")
   