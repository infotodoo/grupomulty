# -*- coding: utf-8 -*-
# Copyright 2021 Diego Carvajal <Github@diegoivanc>


from odoo import fields, models


class AccountTaxGroup(models.Model):
	_inherit = "account.tax.group"

	is_einvoicing = fields.Boolean(
		string="Does it Apply for E-Invoicing?",
		default=True)
