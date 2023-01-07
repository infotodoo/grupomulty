# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _


class AccountInvoice(models.Model):
	_inherit = "account.move"

	discrepancy_response_code_id   = fields.Many2one(
		comodel_name='account.invoice.discrepancy.response.code',
		string='Correction concept for Refund Invoice',)

	refund_type = fields.Selection(
		[('debit', 'Debit Note'),
		 ('credit', 'Credit Note')],
		index=True,
		string='Refund Type',
		track_visibility='always')
	debit_origin_id = fields.Many2one('account.move', 'Factura Debitada', readonly=True, copy=False)
	debit_note_ids = fields.One2many('account.move', 'debit_origin_id', 'Notas Débito', help="Las notas débito creadas a esta factura")
	debit_note_count = fields.Integer('Número de notas débito', compute='_compute_debit_count')

	@api.depends('debit_note_ids')
	def _compute_debit_count(self):
		debit_data = self.env['account.move'].read_group([('debit_origin_id', 'in', self.ids)],
		                                                ['debit_origin_id'], ['debit_origin_id'])
		data_map = {datum['debit_origin_id'][0]: datum['debit_origin_id_count'] for datum in debit_data}
		for inv in self:
			inv.debit_note_count = data_map.get(inv.id, 0.0)
	
	def action_view_debit_notes(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': _('Notas Débito'),
			'res_model': 'account.move',
			'view_mode': 'tree,form',
			'domain': [('debit_origin_id', '=', self.id)],
		}
	
	def _get_sequence(self):
		''' Return the sequence to be used during the post of the current move.
		:return: An ir.sequence record or False.
		'''
		
		res = super(AccountInvoice, self)._get_sequence()
		journal = self.journal_id
		if self.move_type == 'out_invoice' and self.refund_type == 'debit' and journal.debit_note_sequence_id:
			return journal.debit_note_sequence_id
		return res



