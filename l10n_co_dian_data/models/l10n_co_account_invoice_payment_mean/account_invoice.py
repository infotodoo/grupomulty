# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):
	_inherit = "account.move"

	def _get_zzz(self):
		zz_id = False
		if self.sudo().env['ir.model'].search([('model','=','account.payment.mean.code')]):
			zz_id = self.env['account.payment.mean.code'].search([('code','=','ZZZ')])
		if zz_id:
			return zz_id.id
		return False

	payment_mean_id = fields.Many2one(
		comodel_name='account.payment.mean',
		string='Payment Method',
		copy=False,
		default=False)

	payment_mean_code_id = fields.Many2one('account.payment.mean.code',
		string='Mean of Payment',
		copy=False,
		default=_get_zzz)
	invoice_date = fields.Date(default=fields.Date.today()) # datetime.now().date()


	def write(self, vals):
		res = super(AccountInvoice, self).write(vals)

		if vals.get('invoice_date'):
			for invoice in self:
				invoice._onchange_invoice_dates()
		
		return res
	
	@api.model
	def create(self, vals):
		res = super(AccountInvoice, self).create(vals)
		res._onchange_recompute_dynamic_lines()
		res._onchange_invoice_dates()
		return res

	@api.onchange('invoice_date', 'invoice_date_due', 'invoice_payment_term_id')
	def _onchange_invoice_dates(self):
		payment_mean_obj = self.env['ir.model.data']
		time = 0
		invoice_date = self.invoice_date if self.invoice_date else fields.Date.context_today(self)
		if self.invoice_payment_term_id:
			time = sum([x.days for x in self.invoice_payment_term_id.line_ids])
		
		if (invoice_date == self.invoice_date_due and not self.invoice_payment_term_id) \
			or (self.invoice_payment_term_id and time == 0):
			id_payment_mean = payment_mean_obj.get_object_reference(
				'l10n_co_dian_data',
				'account_payment_mean_1')[1]
			payment_mean_id = self.env['account.payment.mean'].browse(id_payment_mean)
		else:
			id_payment_mean = payment_mean_obj.get_object_reference(
				'l10n_co_dian_data',
				'account_payment_mean_2')[1]
			payment_mean_id = self.env['account.payment.mean'].browse(id_payment_mean)

		self.payment_mean_id = payment_mean_id
	
	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		res = super(AccountInvoice, self)._onchange_partner_id()
		self._onchange_invoice_dates()
		return res
