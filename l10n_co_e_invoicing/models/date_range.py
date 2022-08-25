# -*- coding: utf-8 -*-
# Copyright 2021 diego carvajal <Github@Diegoivanc>

from odoo import models, fields


class DateRange(models.Model):
    _inherit = 'date.range'

    out_invoice_sent = fields.Integer(string='Invoices Sent', default=0)
    out_refund_credit_sent = fields.Integer(string='Credit Notes Sent', default=0)
    out_refund_debit_sent = fields.Integer(string='Debit Notes Sent', default=0)