# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import MissingError, UserError, ValidationError, AccessError


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    num_part = fields.Char(string='Número de partes', compute='_compute_num_part')

    @api.depends('product_id')
    def _compute_num_part(self):
        for line in self:
            line.num_part = line.product_id.num_part