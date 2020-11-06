# -*- coding: utf-8 -*-

from odoo import models, fields

class StockMoveMulti(models.Model):

    _inherit = "stock.move"
    _description = "Movimientos de Existencias"
    zone = fields.Many2one('res.partner.zone', string="Zona", store=True, related="picking_id.zone")
    weight = fields.Float(string="Secuencia por Peso")