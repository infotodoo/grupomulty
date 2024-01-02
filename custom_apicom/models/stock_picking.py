# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import MissingError, UserError, ValidationError, AccessError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    observation_ref_intro = fields.Text(string='Texto de Informacion General para Entregas y Pedidos', default=lambda self: self.env.company.observation_ref_intro)