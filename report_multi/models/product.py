# -*- coding: utf-8 -*-

from odoo import models, fields

class ProductMulti(models.Model):

    _inherit = "product.product"
    _description = "Productos"
    zone = fields.Many2one('res.partner.zone', string="Zona")