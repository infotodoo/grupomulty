from odoo import models, fields, api, osv, _
import logging
import qrcode
import io
from base64 import b64encode, b64decode
_logger = logging.getLogger(__name__)
import json

class PosOrder(models.Model):
    _name = "pos.order"
    _inherit = "pos.order"

    type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('out_refund', 'Customer Refund')
    ], readonly=True, default='out_invoice')
    resolution_number = fields.Char('Resolution number in order')
    resolution_date = fields.Date()
    resolution_date_to = fields.Date()
    resolution_number_from = fields.Integer("")
    resolution_number_to = fields.Integer("")

    @api.model
    def pos_customized_sequence(self, sequence):
        sequence = self.env['ir.sequence'].sudo().browse([sequence])
        return sequence.next_by_id()

    @api.model
    def pos_customized_sequence_data(self, sequence):
        sequencias = self.env['ir.sequence'].sudo().browse([sequence])
        sequence_date = self.env['ir.sequence.date_range'].sudo().search([('sequence_id','=',sequence)])

        data = {'resolution_number':sequence_date.resolution_number, 'date_from':sequence_date.date_from,
                'date_to':sequence_date.date_to, 'number_from':sequence_date.number_from,
                'number_to':sequence_date.number_to,
                'secuencia':sequencias.next_by_id()}

        return data

    @api.model
    def _order_fields(self, ui_order):
        if 'new_name' in ui_order:
            ui_order['name'] = ui_order['new_name']
        return super(PosOrder, self)._order_fields(ui_order)

class PosConfig(models.Model):
    _inherit = 'pos.config'

    customized_sequence_id = fields.Many2one('ir.sequence', 'Customized Order Sequence')

