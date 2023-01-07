# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class AccountDebitNote(models.TransientModel):
    """
    Add Debit Note wizard: when you want to correct an invoice with a positive amount.
    Opposite of a Credit Note, but different from a regular invoice as you need the link to the original invoice.
    In some cases, also used to cancel Credit Notes
    """
    _name = 'account.debit.note'
    _description = 'Add Debit Note wizard'
    _inherit = 'account.debit.note'


    def _prepare_default_values(self, move):
        if move.move_type in ('in_refund', 'out_refund'):
            type = 'in_invoice' if move.move_type == 'in_refund' else 'out_invoice'
        else:
            type = move.move_type
        default_values = {
                'ref': '%s, %s' % (move.name, self.reason) if self.reason else move.name,
                'date': self.date or move.date,
                'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
                'journal_id': self.journal_id and self.journal_id.id or move.journal_id.id,
                'invoice_payment_term_id': None,
                'debit_origin_id': move.id,
                'move_type': type,
                'refund_type': 'debit',
            }
        if not self.copy_lines or move.move_type in [('in_refund', 'out_refund')]:
            default_values['line_ids'] = [(5, 0, 0)]

        _logger.info('entro a debit')
        return default_values