# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_support_document = fields.Boolean(string='Documento Soporte?')
    is_support_document_refund = fields.Boolean(string='Devolución Documento Soporte')
