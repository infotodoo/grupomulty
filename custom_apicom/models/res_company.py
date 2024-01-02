# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import MissingError, UserError, ValidationError, AccessError


class ResCompany(models.Model):
    _inherit = 'res.company'

    observation_ref_intro = fields.Text(string='Texto de Informacion General para Entregas y Pedidos')