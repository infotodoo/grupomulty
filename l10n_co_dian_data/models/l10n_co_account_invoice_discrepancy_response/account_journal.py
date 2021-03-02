# -*- coding: utf-8 -*-
# Copyright 2017 Marlon Falcón Hernandez
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _


class AccountJournal(models.Model):
    _inherit = "account.journal"

    debit_note_sequence = fields.Boolean(
        string="Dedicated Debit Note Sequence",
        help="Check this box if you don't want to share the same sequence for invoices and debit "
             "notes made from this journal",
        default=False)
    debit_note_sequence_id = fields.Many2one(
        comodel_name="ir.sequence",
        string="Debit Note Entry Sequence",
        help="This field contains the information related to the numbering of the debit note "
             "entries of this journal.",
        copy=False)
    debit_note_sequence_number_next = fields.Integer(string='Debit Notes Next Number',
        help='The next sequence number will be used for the next Debit note.',
        compute='_compute_debit_seq_number_next',
        inverse='_inverse_debit_seq_number_next')
    
    # do not depend on 'refund_sequence_id.date_range_ids', because
    # refund_sequence_id._get_current_sequence() may invalidate it!
    @api.depends('debit_note_sequence_id.use_date_range', 'debit_note_sequence_id.number_next_actual')
    def _compute_debit_seq_number_next(self):
        '''Compute 'sequence_number_next' according to the current sequence in use,
        an ir.sequence or an ir.sequence.date_range.
        '''
        for journal in self:
            if journal.debit_note_sequence_id and journal.debit_note_sequence:
                sequence = journal.debit_note_sequence_id._get_current_sequence()
                journal.debit_note_sequence_number_next = sequence.number_next_actual
            else:
                journal.debit_note_sequence_number_next = 1

    def _inverse_debit_seq_number_next(self):
        '''Inverse 'debit_note_sequence_number_next' to edit the current sequence next number.
        '''
        for journal in self:
            if journal.debit_note_sequence_id and journal.debit_note_sequence and journal.debit_note_sequence_number_next:
                sequence = journal.debit_note_sequence_id._get_current_sequence()
                sequence.sudo().number_next = journal.debit_note_sequence_number_next

    def write(self, vals):
        if vals.get('refund_sequence'):
            for journal in self.filtered(
                    lambda j: j.type in ('sale', 'purchase')
                              and not j.refund_sequence_id):
                journal_vals = {
                    'name': _('Credit Note Sequence - ') + journal.name,
                    'company_id': journal.company_id.id,
                    'code': journal.code}
                journal.refund_sequence_id = self.sudo()._create_sequence(
                    journal_vals,
                    refund=True).id

        if vals.get('debit_note_sequence'):
            for journal in self.filtered(
                    lambda j: j.type in ('sale', 'purchase')
                              and not j.debit_note_sequence_id):
                journal_vals = {
                    'name': _('Debit Note Sequence - ') + journal.name,
                    'company_id': journal.company_id.id,
                    'code': journal.code}
                journal.debit_note_sequence_id = self.sudo()._create_sequence(
                    journal_vals,
                    refund=True).id

        return super(AccountJournal, self).write(vals)