from odoo import models, fields, api, _
import logging

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    trm_currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        default=lambda self: self.env.company,
        tracking=True)
    use_trm = fields.Boolean(
        string="TRM?",
        tracking=True)
    trm_rate = fields.Monetary(
        currency_field='trm_currency_id',
        string="TRM",
        tracking=True)
    tariff = fields.Monetary(
        currency_field='trm_currency_id',
        string="Tarifa",
        tracking=True)
