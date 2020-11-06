# -*- coding: utf-8 -*-

from odoo import models, fields

class StockPickingMulti(models.Model):

    _inherit = "stock.picking"
    _description = "Stock Picking"
    zone = fields.Many2one('res.partner.zone', string="Zona", related="partner_id.zone")