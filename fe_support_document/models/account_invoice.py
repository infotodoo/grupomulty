# -*- coding: utf-8 -*-
# Copyright 2019 Diego Carvajak <Github@Diegoivanc>
from datetime import datetime, timedelta
from pytz import timezone
import zipfile
from io import BytesIO

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, format_date, get_lang
from base64 import b64encode, b64decode
import base64
import re
import uuid
from . import global_functions

import logging
_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
	_inherit = "account.move"

	operation_type_supplier = fields.Selection([('10', 'Residente'), ('11', 'No Residente')], string='Operation Type', default='10')

	def post(self, soft=True):
		for record in self:
			if record.state != 'draft':
				raise ValidationError(_('Esta factura [%s] no está en borrador, por lo tanto, no se puede publicar. \n' \
										'Por favor, recargue la página para refrescar el estado de esta factura.') % record.id)

		res = super(AccountInvoice, self).post()

		for record in self:
			if record.company_id.einvoicing_enabled:
				if record.type == "in_invoice" and record.journal_id.is_support_document:
					dian_document_obj = self.env['account.invoice.dian.document']
					dian_document = dian_document_obj.create({
						'invoice_id': record.id,
						'company_id': record.company_id.id,
						'type_account': 'invoice'
					})
					dian_document.support_document()
					self.approve_token = self.approve_token if self.approve_token else str(uuid.uuid4())
				if record.type == "in_refund" and record.journal_id.is_support_document:
					dian_document_obj = self.env['account.invoice.dian.document']
					dian_document = dian_document_obj.create({
						'invoice_id': record.id,
						'company_id': record.company_id.id,
						'type_account': 'invoice'
					})
					dian_document.support_document_refund()
					self.approve_token = self.approve_token if self.approve_token else str(uuid.uuid4())
		return res