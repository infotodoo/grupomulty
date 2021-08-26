# -*- coding: utf-8 -*-
# Copyright 2019 Diego Carvajak <Github@Diegoivanc>
# Copyright 2019 Joan Marín <Github@joanmarin>
# Copyright 2019 Diego Carvajal <Github@diegoivanc>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang
from base64 import b64encode, b64decode
import base64
import re
from . import global_functions

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
	_inherit = "account.move"

	dian_document_lines = fields.One2many(
		comodel_name='account.invoice.dian.document',
		inverse_name='invoice_id',
		string='Dian Document Lines')

	operation_type = fields.Selection(
		[('09', 'AIU'),
		 ('10', 'Standard *'),
		 ('11', 'Mandatos'),
		 ('20', 'Credit note that references an e-invoice'),
		 ('22', 'Credit note without reference to invoices *'),
		 ('30', 'Debit note that references an e-invoice'),
		 ('32', 'Debit note without reference to invoices *')],
		string='Operation Type',
		default='10')
	invoice_type_code = fields.Selection(
		[('01', 'Factura de Venta'),
		 ('02', 'Factura de Venta Exportación'),
		 ('03', 'Factura por Contingencia Facturador'),
		 ('04', 'Factura por Contingencia DIAN')],
		string='Invoice Type',
		default='01')
	send_invoice_to_dian = fields.Selection(
		[('0', 'Immediately'),
		 ('1', 'After 1 Day'),
		 ('2', 'After 2 Days')],
		string='Send Invoice to DIAN?',
		default='0')

	trm = fields.Float()
	is_invoice_out_odoo = fields.Boolean('Creada fuera de odoo?')
	id_invoice_refound = fields.Char('Factura')
	uuid_invoice = fields.Char('Cufe')
	issue_date_invoice = fields.Date('Fecha')
	customizationid_invoice = fields.Integer(string="Tipo de operación Factura", default=10)
	aiu = fields.Char(string='AIU')

	credit_note_ids = fields.One2many('account.move', 'reversed_entry_id', string="Notas crédito")

	credit_note_count = fields.Integer('Number of Credit Notes', compute='_compute_credit_count')
	mandante_id = fields.Many2one('res.partner', string="Mandante")

	@api.depends('credit_note_ids')
	def _compute_credit_count(self):
		credit_data = self.env['account.move'].read_group([('reversed_entry_id', 'in', self.ids)],
															['reversed_entry_id'], ['reversed_entry_id'])
		data_map = {datum['reversed_entry_id'][0]: datum['reversed_entry_id_count'] for datum in credit_data}
		for inv in self:
			inv.credit_note_count = data_map.get(inv.id, 0.0)

	def action_view_credit_notes(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': _('Notas Crédito'),
			'res_model': 'account.move',
			'view_mode': 'tree,form',
			'domain': [('reversed_entry_id', '=', self.id)],
		}

	def post(self):
		_logger.info('validatee')
		_logger.info('validatee')
		_logger.info('validatee')
		_logger.info('validatee')

		res = super(AccountInvoice, self).post()
		for record in self:

			if record.company_id.einvoicing_enabled and record.journal_id.is_einvoicing:
				if record.type in ("out_invoice", "out_refund"):
					if len(self) > 1:
						raise ValidationError(_('No está permitido publicar más de una factura electrónica a la vez.'))
					company_currency = record.company_id.currency_id
					rate = 1
					# date = self._get_currency_rate_date() or fields.Date.context_today(self)
					date = fields.Date.context_today(self)

					if record.currency_id.id != company_currency.id:
						currency = record.currency_id
						_logger.info(currency)
						rate = currency._convert(rate, company_currency, record.company_id, date)

						record.trm = rate

					if record.type == 'out_invoice' and record.refund_type == 'debit':
						type_account = 'debit'
					elif record.type == 'out_refund' and record.refund_type != 'debit':
						type_account = 'credit'
					else:
						type_account = 'invoice'

					dian_document_obj = self.env['account.invoice.dian.document']
					dian_document = False
					dian_document = dian_document_obj.create({
						'invoice_id': record.id,
						'company_id': record.company_id.id,
						'type_account': type_account
					})
					dian_document.action_set_files()

					if record.send_invoice_to_dian == '0':
						if record.invoice_type_code in ('01', '02', '03'):
							dian_document.action_sent_zipped_file()
						elif record.invoice_type_code == '04':
							dian_document.action_send_mail()

		return res

	def _get_pdf_file(self):
		template = self.env['ir.actions.report'].browse(self.dian_document_lines.company_id.report_template.id)
		# pdf = self.env.ref('account.move').render_qweb_pdf([self.invoice_id.id])[0]
		if template:
			pdf = template.render_qweb_pdf(self.id)[0]
		else:
			pdf = self.env.ref('account.account_invoices').render_qweb_pdf(self.id)[0]
		pdf = base64.b64encode(pdf)
		pdf_name = re.sub(r'\W+', '', self.name) + '.pdf'

		return pdf

	def action_invoice_sent(self):
		""" Open a window to compose an email, with the edi invoice template
			message loaded by default
		"""
		self.ensure_one()
		template = self.env.ref('l10n_co_e_invoicing.email_template_for_einvoice')
		# template = self.env.ref('account.email_template_edi_invoice', raise_if_not_found=False)

		xml_attachment_file = False
		if self.dian_document_lines[0].ar_xml_file and self.dian_document_lines[0].xml_file:
			xml_without_signature = global_functions.get_template_xml(
				self.dian_document_lines._get_attachment_values(),
				'attachment')

			xml_attachment_file = self.env['ir.attachment'].create({
				'name': self.name + '-attachment.xml',
				'type': 'binary',
				'datas': b64encode(xml_without_signature.encode()).decode("utf-8", "ignore")})


		xml_attachment = self.env['ir.attachment'].create({
			'name': self.dian_document_lines.xml_filename,
			'type': 'binary',
			'datas': self.dian_document_lines.xml_file})
		pdf_attachment = self.env['ir.attachment'].create({
			'name': self.name + '.pdf',
			'type': 'binary',
			'datas': self._get_pdf_file()})

		attach_ids = [(xml_attachment.id),(pdf_attachment.id)]
		if xml_attachment_file:
			attach_ids.append((xml_attachment_file.id))

		template.attachment_ids = [(6, 0, attach_ids)]

		lang = get_lang(self.env)
		if template and template.lang:
			lang = template._render_template(template.lang, 'account.move', self.id)
		else:
			lang = lang.code
		compose_form = self.env.ref('account.account_invoice_send_wizard_form', raise_if_not_found=False)
		ctx = dict(
			default_model='account.move',
			default_res_id=self.id,
			default_use_template=bool(template),
			default_template_id=template and template.id or False,
			default_composition_mode='comment',
			mark_invoice_as_sent=True,
			custom_layout="mail.mail_notification_paynow",
			model_description=self.with_context(lang=lang).type_name,
			force_email=True
		)

		return {
			'name': _('Send Invoice'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'account.invoice.send',
			'views': [(compose_form.id, 'form')],
			'view_id': compose_form.id,
			'target': 'new',
			'context': ctx,
		}

	def invoice_validate(self):
		_logger.info('validatee')
		_logger.info('validatee')
		_logger.info('validatee')
		_logger.info('validatee')

		res = super(AccountInvoice, self).invoice_validate()

		if self.company_id.einvoicing_enabled:
			if self.type != "in_invoice":
				dian_document_obj = self.env['account.invoice.dian.document']
				dian_document = dian_document_obj.create({
					'invoice_id': self.id,
					'company_id': self.company_id.id})
				dian_document.set_files()
				dian_document.sent_zipped_file()
				dian_document.GetStatusZip()

		return res

	def action_invoice_print(self):
		""" Print the invoice and mark it as sent, so that we can see more
			easily the next step of the workflow
		"""
		if any(not move.is_invoice(include_receipts=True) for move in self):
			raise UserError(_("Only invoices could be printed."))

		self.filtered(lambda inv: not inv.invoice_sent).write({'invoice_sent': True})
		"""
		if self.user_has_groups('account.group_account_invoice'):
			return self.env.ref('account.account_invoices').report_action(self)
		else:
			return self.env.ref('account.account_invoices_without_payment').report_action(self)
		"""
		return self.env.ref('l10n_co_e_invoicing.account_e_invoices').report_action(self)

	def _get_payment_exchange_rate(self):
		company_currency = self.company_id.currency_id
		rate = 1
		#date = self._get_currency_rate_date() or fields.Date.context_today(self)
		date =  fields.Date.context_today(self)
		_logger.info(self.currency_id)
		_logger.info(company_currency)
		if self.currency_id.id != company_currency.id:
			currency =self.currency_id
			_logger.info(currency)
			rate = currency._convert(rate, company_currency,self.company_id,date)
			_logger.info(rate)

		return {
			'SourceCurrencyCode': self.currency_id.name,
			'TargetCurrencyCode': company_currency.name,
			'CalculationRate': rate,
			'Date': date}

	def action_cancel(self):
		res = super(AccountInvoice, self).action_cancel()

		for dian_document in self.dian_document_lines:
			if dian_document.state == 'done':
				raise UserError('You cannot cancel a invoice sent to DIAN')

		return res

	def _get_billing_reference(self):
		billing_reference = {}
		msg1 = ''
		msg2 = _('La nota %s no tiene referencia de facturación \n\n') % 'crédito' if self.refund_type == 'credit' else 'débito' if self.refund_type == 'debit' else ''
		#for origin_invoice in self.refund_invoice_id:
		_logger.info(self.reversed_entry_id)
		origin_invoice_id = self.reversed_entry_id if self.refund_type == 'credit' else self.debit_origin_id if self.refund_type == 'debit' else False
		for origin_invoice in origin_invoice_id:
			_logger.info('refund')
			_logger.info(origin_invoice)
			if origin_invoice.state in ('open', 'paid', 'posted'):
				for dian_document in origin_invoice.dian_document_lines:
					if dian_document.state == 'done':
						billing_reference['ID'] = origin_invoice.name
						billing_reference['UUID'] = dian_document.cufe_cude
						billing_reference['IssueDate'] = origin_invoice.invoice_date
						billing_reference['CustomizationID'] = origin_invoice.operation_type
					else:
						msg1 = _('El documento DIAN de la factura %s no está procesado correctamente. Por favor, validar su estado en la DIAN.') % origin_invoice.name

		if not billing_reference:
			raise UserError(msg2 + msg1)
		else:
			return billing_reference



	def _get_active_dian_resolution(self):
		msg = _("You do not have an active dian resolution, "
				"contact with your administrator.")
		resolution_number = False
		date_from = False
		date_to = False
		number_from = False
		number_to = False
		technical_key = False

		for date_range_id in self.journal_id.sequence_id.date_range_ids:
			if date_range_id.active_resolution:
				resolution_number = date_range_id.resolution_number
				date_from = date_range_id.date_from
				date_to = date_range_id.date_to
				number_from = date_range_id.number_from
				number_to = date_range_id.number_to
				technical_key = date_range_id.technical_key
				break

		if not resolution_number:
			raise UserError(msg)

		return {
			'prefix': self.journal_id.sequence_id.prefix or '',
			'resolution_number': resolution_number,
			'date_from': date_from,
			'date_to': date_to,
			'number_from': number_from,
			'number_to': number_to,
			'technical_key': technical_key}

	def _get_einvoicing_taxes(self):

		msg1 = _("Your tax: '%s', has no e-invoicing tax group type, " +
				 "contact with your administrator.")
		msg2 = _("Your withholding tax: '%s', has amount equal to zero (0), the withholding taxes " +
				 "must have amount different to zero (0), contact with your administrator.")
		msg3 = _("Your tax: '%s', has negative amount or an amount equal to zero (0), the taxes " +
				 "must have an amount greater than zero (0), contact with your administrator.")
		taxes = {}
		withholding_taxes = {}
		company_currency = self.company_id.currency_id

		for tax in self.line_ids:
			_logger.info("tax.tax_line_id.amount")
			_logger.info("tax.tax_line_id.amount")
			_logger.info("tax.tax_line_id.amount")
			_logger.info("tax.tax_line_id.amount")
			_logger.info(tax.tax_line_id.amount)
			_logger.info(tax.tax_line_id.tax_group_id)
			_logger.info(tax.tax_line_id.tax_group_id.is_einvoicing)

			if tax.tax_line_id.tax_group_id.is_einvoicing:
				if not tax.tax_line_id.tax_group_id.tax_group_type_id:
					raise UserError(msg1 % tax.name)

				tax_code = tax.tax_line_id.tax_group_id.tax_group_type_id.code
				tax_name = tax.tax_line_id.tax_group_id.tax_group_type_id.name
				tax_type = tax.tax_line_id.tax_group_id.tax_group_type_id.type
				rate = 1
				date = fields.Date.context_today(self)
				# tax_percent = '{:.2f}'.format(tax.tax_line_id.amount)
				tax_percent = str('{:.2f}'.format(tax.tax_line_id.amount))

				if tax_type == 'withholding_tax' and tax.tax_line_id.amount == 0:
					raise UserError(msg2 % tax.name)
				elif tax_type == 'tax' and tax.tax_line_id.amount < 0:
					raise UserError(msg3 % tax.name)
				# elif tax_type == 'tax' and tax.tax_line_id.amount == 0:
				# 	pass
				elif tax_type == 'withholding_tax' and tax.tax_line_id.amount < 0:
					if tax_code not in withholding_taxes:
						withholding_taxes[tax_code] = {}
						withholding_taxes[tax_code]['total'] = 0
						withholding_taxes[tax_code]['name'] = tax_name
						withholding_taxes[tax_code]['taxes'] = {}

					if float(tax_percent) < 0.0:
						tax_percent = str('{:.3f}'.format(tax.tax_line_id.amount * (-1)))
						# tax_percent = str(tax.tax_line_id.amount*(-1))
						_logger.info('tax_percent')
						_logger.info('tax_percent')
						_logger.info(tax_percent)

					if tax_percent not in withholding_taxes[tax_code]['taxes']:
						withholding_taxes[tax_code]['taxes'][tax_percent] = {}
						withholding_taxes[tax_code]['taxes'][tax_percent]['base'] = 0
						withholding_taxes[tax_code]['taxes'][tax_percent]['amount'] = 0

					if self.currency_id.id != company_currency.id:
						currency = self.currency_id
						# _logger.info(currency)
						rate = currency._convert(rate, company_currency, self.company_id, date)
						withholding_taxes[tax_code]['total'] += (((
																			  tax.tax_base_amount / rate) * tax.tax_line_id.amount) / 100) * (
																	-1)
						withholding_taxes[tax_code]['taxes'][tax_percent]['base'] += tax.tax_base_amount / rate
						withholding_taxes[tax_code]['taxes'][tax_percent]['amount'] += (((
																									 tax.tax_base_amount / rate) * tax.tax_line_id.amount) / 100) * (
																						   -1)
					else:
						withholding_taxes[tax_code]['total'] += ((
																			 tax.tax_base_amount * tax.tax_line_id.amount) / 100) * (
																	-1)
						withholding_taxes[tax_code]['taxes'][tax_percent]['base'] += tax.tax_base_amount
						withholding_taxes[tax_code]['taxes'][tax_percent]['amount'] += ((
																									tax.tax_base_amount * tax.tax_line_id.amount) / 100) * (
																						   -1)

				elif tax_type == 'withholding_tax' and tax.tax_line_id.amount > 0:
					# TODO 3.0 Las retenciones se recomienda no enviarlas a la DIAN
					# Solo las positivas que indicarian una autoretencion, Si la DIAN
					# pide que se envien las retenciones, seria quitar o comentar este if
					pass
				else:
					if tax_code not in taxes:
						taxes[tax_code] = {}
						taxes[tax_code]['total'] = 0
						taxes[tax_code]['name'] = tax_name
						taxes[tax_code]['taxes'] = {}

					if tax_percent not in taxes[tax_code]['taxes']:
						taxes[tax_code]['taxes'][tax_percent] = {}
						taxes[tax_code]['taxes'][tax_percent]['base'] = 0
						taxes[tax_code]['taxes'][tax_percent]['amount'] = 0

					# date = self._get_currency_rate_date() or fields.Date.context_today(self)
					if self.currency_id.id != company_currency.id:
						currency = self.currency_id
						rate = currency._convert(rate, company_currency, self.company_id, date)
						taxes[tax_code]['total'] += (((tax.tax_base_amount / rate) * tax.tax_line_id.amount) / 100)
						taxes[tax_code]['taxes'][tax_percent]['base'] += tax.tax_base_amount / rate
						taxes[tax_code]['taxes'][tax_percent]['amount'] += (
									((tax.tax_base_amount / rate) * tax.tax_line_id.amount) / 100)
					else:
						taxes[tax_code]['total'] += ((tax.tax_base_amount * tax.tax_line_id.amount) / 100)
						taxes[tax_code]['taxes'][tax_percent]['base'] += tax.tax_base_amount
						taxes[tax_code]['taxes'][tax_percent]['amount'] += (
									(tax.tax_base_amount * tax.tax_line_id.amount) / 100)

		# if '01' not in taxes:
		# 	taxes['01'] = {}
		# 	taxes['01']['total'] = 0
		# 	taxes['01']['name'] = 'IVA'
		# 	taxes['01']['taxes'] = {}
		# 	taxes['01']['taxes']['0.00'] = {}
		# 	taxes['01']['taxes']['0.00']['base'] = 0
		# 	taxes['01']['taxes']['0.00']['amount'] = 0

		# if '03' not in taxes:
		# 	taxes['03'] = {}
		# 	taxes['03']['total'] = 0
		# 	taxes['03']['name'] = 'ICA'
		# 	taxes['03']['taxes'] = {}
		# 	taxes['03']['taxes']['0.00'] = {}
		# 	taxes['03']['taxes']['0.00']['base'] = 0
		# 	taxes['03']['taxes']['0.00']['amount'] = 0
		#
		# if '04' not in taxes:
		# 	taxes['04'] = {}
		# 	taxes['04']['total'] = 0
		# 	taxes['04']['name'] = 'INC'
		# 	taxes['04']['taxes'] = {}
		# 	taxes['04']['taxes']['0.00'] = {}
		# 	taxes['04']['taxes']['0.00']['base'] = 0
		# 	taxes['04']['taxes']['0.00']['amount'] = 0

		return {'TaxesTotal': taxes, 'WithholdingTaxesTotal': withholding_taxes}
	# def _get_accounting_supplier_party_values(self):
	# 	msg1 = _("'%s' does not have a person type assigned")
	# 	msg2 = _("'%s' does not have a state assigned")
	# 	msg3 = _("'%s' does not have a country assigned")
	#
	# 	if self.type in ('out_invoice', 'out_refund'):
	# 		supplier = self.company_id.partner_id
	# 	else:
	# 		supplier = self.partner_id
	#
	# 	if not supplier.person_type:
	# 		raise UserError(msg1 % supplier.name)
	#
	# 	if supplier.country_id:
	# 		if supplier.country_id.code == 'CO' and not  supplier.state_id:
	# 			raise UserError(msg2 % supplier.name)
	# 	else:
	# 		raise UserError(msg3 % supplier.name)
	#
	# 	return {
	# 		'AdditionalAccountID': supplier.person_type,
	# 		'Name': supplier.name,
	# 		'AddressID':  supplier.zip_id.dian_code or '',
	# 		'AddressCityName':  supplier.zip_id.city_id.name or '',
	# 		'AddressPostalZone':  supplier.zip_id.dian_code or '',
	# 		'AddressCountrySubentity': supplier.state_id.name or '',
	# 		'AddressCountrySubentityCode': supplier.state_id.code,
	# 		'AddressLine': supplier.street or '',
	# 		'CompanyIDschemeID': supplier.check_digit,
	# 		'CompanyIDschemeName': supplier.document_type_id.code,
	# 		'CompanyID': supplier.identification_document,
	# 		'TaxLevelCode': supplier.property_account_position_id.tax_level_code_id.code,
	# 		'TaxSchemeID': supplier.property_account_position_id.tax_scheme_id.code,
	# 		'TaxSchemeName': supplier.property_account_position_id.tax_scheme_id.name,
	# 		'CorporateRegistrationSchemeName': supplier.ref,
	# 		'CountryIdentificationCode': supplier.country_id.code,
	# 		'CountryName': supplier.country_id.name}

	# def _get_accounting_customer_party_values(self):
	# 	msg1 = _("'%s' does not have a person type assigned")
	# 	msg2 = _("'%s' does not have a state assigned")
	# 	msg3 = _("'%s' does not have a country assigned")
	#
	# 	if self.type in ('in_refund'):
	# 		customer = self.company_id.partner_id
	# 	else:
	# 		customer = self.partner_id
	#
	# 	if not customer.person_type:
	# 		raise UserError(msg1 % customer.name)
	#
	# 	if customer.country_id:
	# 		if customer.country_id.code == 'CO' and not customer.state_id:
	# 			raise UserError(msg2 % customer.name)
	# 	else:
	# 		raise UserError(msg3 % customer.name)
	#
	# 	return {
	# 		'AdditionalAccountID': customer.person_type,
	# 		'Name': customer.name,
	# 		'AddressID':  customer.zip_id.dian_code or '',
	# 		'AddressCityName':  customer.zip_id.city_id.name or '',
	# 		'AddressPostalZone':  customer.zip_id.dian_code or '',
	# 		'AddressCountrySubentity': customer.state_id.name or '',
	# 		'AddressCountrySubentityCode': customer.state_id.code,
	# 		'AddressLine': customer.street  or '',
	# 		'CompanyIDschemeID': customer.check_digit,
	# 		'CompanyIDschemeName': customer.document_type_id.code,
	# 		'CompanyID': customer.identification_document,
	# 		'TaxLevelCode': customer.property_account_position_id.tax_level_code_id.code,
	# 		'TaxSchemeID': customer.property_account_position_id.tax_scheme_id.code,
	# 		'TaxSchemeName': customer.property_account_position_id.tax_scheme_id.name,
	# 		'CorporateRegistrationSchemeName': customer.ref,
	# 		'CountryIdentificationCode': customer.country_id.code,
	# 		'CountryName': customer.country_id.name}

	def _get_tax_representative_party_values(self):
		if self.type in ('out_invoice', 'out_refund'):
			supplier = self.company_id.partner_id
		else:
			supplier = self.partner_id

		return {
			'IDschemeID': supplier.check_digit,
			'IDschemeName': supplier.document_type_id.code,
			'ID': supplier.identification_document}


	def _get_invoice_lines(self):
		msg1 = _("Your Unit of Measure: '%s', has no Unit of Measure Code, " +
				 "contact with your administrator.")
		msg2 = _("The invoice line %s has no reference")
		msg3 = _("Your product: '%s', has no reference price, " +
				 "contact with your administrator.")
		msg4 = _("Your tax: '%s', has no e-invoicing tax group type, " +
				 "contact with your administrator.")
		msg5 = _("Your withholding tax: '%s', has amount equal to zero (0), the withholding taxes " +
				 "must have amount different to zero (0), contact with your administrator.")
		msg6 = _("Your tax: '%s', has negative amount or an amount equal to zero (0), the taxes " +
				 "must have an amount greater than zero (0), contact with your administrator.")

		invoice_lines = {}
		count = 1

		for invoice_line in self.invoice_line_ids.filtered(lambda x: not x.display_type):
			if not invoice_line.product_uom_id.product_uom_code_id:
				raise UserError(msg1 % invoice_line.product_uom_id.name)

			disc_amount = 0
			total_wo_disc = 0
			brand_name = False
			model_name = False

			if invoice_line.price_subtotal != 0 and invoice_line.discount != 0:
				disc_amount = (invoice_line.price_subtotal * invoice_line.discount) / 100

			if invoice_line.price_unit != 0 and invoice_line.quantity != 0:
				total_wo_disc = invoice_line.price_unit * invoice_line.quantity

			if invoice_line.price_unit == 0 or invoice_line.quantity == 0:
				raise ValidationError(
					_('Para facturación electrónica no está permitido lineas de producto con precio o cantidad en 0.'))

			if not invoice_line.product_id or not invoice_line.product_id.default_code:
				raise UserError(msg2 % invoice_line.name)

			if invoice_line.product_id.margin_percentage > 0:
				reference_price = invoice_line.product_id.margin_percentage
			else:
				reference_price = invoice_line.product_id.margin_percentage * \
								  invoice_line.product_id.standard_price

			if invoice_line.price_subtotal <= 0 and reference_price <= 0:
				raise UserError(msg3 % invoice_line.product_id.default_code)

			# if self.invoice_type_code == '02':
			# 	if invoice_line.product_id.product_brand_id:
			# 		brand_name = invoice_line.product_id.product_brand_id.name

			# 	model_name = invoice_line.product_id.manufacturer_pref
			brand_name = invoice_line.product_id.brand_name or ''
			model_name = invoice_line.product_id.model_name or ''

			product_scheme_id = invoice_line.product_id.product_scheme_id or self.env['product.scheme'].search(
				[('code', '=', '999')])

			nota_ref = ''
			if self.operation_type == '09':
				nota_ref = 'Contrato de servicios AIU por concepto de: ' + self.aiu

			invoice_lines[count] = {}
			invoice_lines[count]['Note'] = nota_ref or ''
			invoice_lines[count]['unitCode'] = invoice_line.product_uom_id.product_uom_code_id.code
			invoice_lines[count]['Quantity'] = '{:.2f}'.format(invoice_line.quantity)
			invoice_lines[count]['PriceAmount'] = '{:.2f}'.format(reference_price)
			invoice_lines[count]['LineExtensionAmount'] = '{:.2f}'.format(invoice_line.price_subtotal)
			invoice_lines[count]['PricingReference'] = '{:.2f}'.format(invoice_line.product_id.standard_price or 0.0)
			invoice_lines[count]['MultiplierFactorNumeric'] = '{:.2f}'.format(invoice_line.discount)
			invoice_lines[count]['AllowanceChargeAmount'] = '{:.2f}'.format(disc_amount)
			invoice_lines[count]['AllowanceChargeBaseAmount'] = '{:.2f}'.format(total_wo_disc)
			invoice_lines[count]['TaxesTotal'] = {}
			invoice_lines[count]['WithholdingTaxesTotal'] = {}
			invoice_lines[count]['SellersItemIdentification'] = invoice_line.product_id.default_code
			invoice_lines[count]['StandardItemIdentification'] = invoice_line.product_id.product_scheme_code or ''
			invoice_lines[count]['StandardschemeID'] = product_scheme_id.code or ''
			invoice_lines[count]['StandardschemeName'] = product_scheme_id.name or ''
			invoice_lines[count]['StandardschemeAgencyID'] = product_scheme_id.scheme_agency_id or ''

			for tax in invoice_line.tax_ids:

				if tax.amount_type == 'group':
					tax_ids = tax.children_tax_ids
				else:
					tax_ids = tax

				for tax_id in tax_ids:
					if tax_id.tax_group_id.is_einvoicing:
						if not tax_id.tax_group_id.tax_group_type_id:
							raise UserError(msg4 % tax.name)

						tax_type = tax_id.tax_group_id.tax_group_type_id.type

						if tax_type == 'withholding_tax' and tax_id.amount == 0:
							raise UserError(msg5 % tax_id.name)
						elif tax_type == 'tax' and tax_id.amount < 0:
							raise UserError(msg6 % tax_id.name)
						elif tax_type == 'tax' and tax_id.amount == 0:
							_logger.info('entra a pass')
							_logger.info('entra a pass')
							_logger.info('entra a pass')
							_logger.info(tax_id.amount)
							pass

						elif tax_type == 'withholding_tax' and tax_id.amount < 0:
							_logger.info('entro a negativo')
							invoice_lines[count]['WithholdingTaxesTotal'] = (
								invoice_line._get_invoice_lines_taxes(
									tax_id,
									abs(tax_id.amount),
									invoice_lines[count]['WithholdingTaxesTotal']))
						elif tax_type == 'withholding_tax' and tax_id.amount > 0:
							# TODO 3.0 Las retenciones se recomienda no enviarlas a la DIAN.
							# Solo la parte positiva que indicaria una autoretencion, Si la DIAN
							# pide que se envie la parte negativa, seria quitar o comentar este if
							pass
						else:
							invoice_lines[count]['TaxesTotal'] = (
								invoice_line._get_invoice_lines_taxes(
									tax_id,
									tax_id.amount,
									invoice_lines[count]['TaxesTotal']))

			if '01' not in invoice_lines[count]['TaxesTotal']:
				invoice_lines[count]['TaxesTotal']['01'] = {}
				invoice_lines[count]['TaxesTotal']['01']['total'] = 0
				invoice_lines[count]['TaxesTotal']['01']['name'] = 'IVA'
				invoice_lines[count]['TaxesTotal']['01']['taxes'] = {}
				invoice_lines[count]['TaxesTotal']['01']['taxes']['0.00'] = {}
				invoice_lines[count]['TaxesTotal']['01']['taxes']['0.00']['base'] = invoice_line.price_subtotal
				invoice_lines[count]['TaxesTotal']['01']['taxes']['0.00']['amount'] = 0

			# if '03' not in invoice_lines[count]['TaxesTotal']:
			# 	invoice_lines[count]['TaxesTotal']['03'] = {}
			# 	invoice_lines[count]['TaxesTotal']['03']['total'] = 0
			# 	invoice_lines[count]['TaxesTotal']['03']['name'] = 'ICA'
			# 	invoice_lines[count]['TaxesTotal']['03']['taxes'] = {}
			# 	invoice_lines[count]['TaxesTotal']['03']['taxes']['0.00'] = {}
			# 	invoice_lines[count]['TaxesTotal']['03']['taxes']['0.00']['base'] = invoice_line.price_subtotal
			# 	invoice_lines[count]['TaxesTotal']['03']['taxes']['0.00']['amount'] = 0
			#
			# if '04' not in invoice_lines[count]['TaxesTotal']:
			# 	invoice_lines[count]['TaxesTotal']['04'] = {}
			# 	invoice_lines[count]['TaxesTotal']['04']['total'] = 0
			# 	invoice_lines[count]['TaxesTotal']['04']['name'] = 'INC'
			# 	invoice_lines[count]['TaxesTotal']['04']['taxes'] = {}
			# 	invoice_lines[count]['TaxesTotal']['04']['taxes']['0.00'] = {}
			# 	invoice_lines[count]['TaxesTotal']['04']['taxes']['0.00']['base'] = invoice_line.price_subtotal
			# 	invoice_lines[count]['TaxesTotal']['04']['taxes']['0.00']['amount'] = 0

			invoice_lines[count]['BrandName'] = brand_name
			invoice_lines[count]['ModelName'] = model_name
			invoice_lines[count]['ItemDescription'] = str(
				invoice_line.name) if invoice_line.name != invoice_line.product_id.display_name else invoice_line.product_id.name or ''
			invoice_lines[count]['InformationContentProviderParty'] = (
				invoice_line._get_information_content_provider_party_values())
			invoice_lines[count]['PriceAmount'] = '{:.2f}'.format(
				invoice_line.price_unit)

			count += 1
		_logger.info('taxestotal')
		_logger.info('taxestotal')
		_logger.info('taxestotal')
		_logger.info(invoice_lines)
		return invoice_lines
