# -*- coding: utf-8 -*-
# Copyright 2019 Juan Camilo Zuluaga Serna <Github@camilozuluaga>
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)



class account_move_line(models.Model):
	_inherit = "account.move.line"

	discount_code = fields.Selection(
		string='Codigos de Descuento',
		selection=[('00', 'Descuento no condicionado'), ],
		required=False)

	reference_code = fields.Selection(
	    string='Cod. Referencia',
	    selection=[('01', 'Valor Comercial'),],
	    required=False, )

	@api.onchange('discount')
	def _compute_discount(self):
		if self.discount:
			if self.discount > 100 or self.discount < 0 :
				raise ValidationError("El descuento debe ser entre 0% y 100%")
			elif self.discount > 0 or self.discount < 100:
				self.discount_code = 00

	@api.onchange('reference_code')
	def _compute_discount(self):
		if self.reference_code:
			if self.reference_code == '01':
				self.price_unit = 1





class AccountInvoice(models.Model):
	_inherit = "account.move"

	discount_code = fields.Selection(
	    string='Codigos de Descuento',
	    selection=[('00', 'Descuento no condicionado'), ],
	    required=False )

