# -- coding: utf-8 --

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging
import json
import os
import sys


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    analytic_id = fields.Many2one('account.analytic.account', string='Cuentas Analiticas',
                                  default=lambda self: self.sale_id.analytic_account_id or None)

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for picking in self:
            for item in picking.move_lines:
                for record in item.account_move_ids:
                    for line in record.line_ids:
                        if line.account_id.code[0] not in (1, 2, 3, '1', '2', '3'):
                            line.analytic_account_id = picking.analytic_id
                    record.mapped('line_ids').create_analytic_lines()
                    record.write({'state': 'posted', 'posted_before': True})
        return res


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        picking = self.env['stock.picking'].search([('sale_id', '=', self.id)])
        for item in picking:
            if item.sale_id:
                item.write({'analytic_id': self.analytic_account_id})
        return res