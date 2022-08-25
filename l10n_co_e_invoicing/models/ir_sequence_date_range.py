# -*- coding: utf-8 -*-
# Copyright 2021 Diego Carvajal <Github@diegoivanc>


from odoo import fields, models


class IrSequenceDateRange(models.Model):
    _inherit = 'ir.sequence.date_range'

    dian_type = fields.Selection(
        string='DIAN Type',
        related='sequence_id.dian_type',
        store=False)
    technical_key = fields.Char(string="Technical Key")
