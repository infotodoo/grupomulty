# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import MissingError, UserError, ValidationError, AccessError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    observation_ref_intro = fields.Text(
        string='Texto de Informacion General para Entregas y Pedidos',
        default=lambda self: self.env.company.observation_ref_intro)

    