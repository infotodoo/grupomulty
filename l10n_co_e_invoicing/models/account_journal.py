# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_einvoicing = fields.Boolean(string='Electronic invoicing?')
    acknowledgement_receipt = fields.Boolean(string='Acuso de Recibo?')
    resolution_text = fields.Text(string='Resolution')
    
