# -*- coding: utf-8 -*-
# LUIS FELIPE PATERNINA VITAL
#Todoo SAS


from odoo import models, fields

class RespartnerType(models.Model):

    _name = "res.partner.type"
    name = fields.Char(string='Descripción', required=True)
    code = fields.Char(string='Código')
    