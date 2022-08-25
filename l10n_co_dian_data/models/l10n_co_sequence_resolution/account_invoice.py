# -*- coding: utf-8 -*-
# Copyright 2016 Dominic Krimmer
# Copyright 2016 Luis Alfredo da Silva (luis.adasilvaf@gmail.com)
# Copyright 2019 Joan Marín <Github@JoanMarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime
from pytz import timezone

from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):
    _inherit = 'account.move'

    def _get_warn_resolution(self):
        warn_remaining = False
        warn_inactive_resolution = False
        days = 0
        numbers = 0
        if self.journal_id.sequence_id.use_dian_control:
            remaining_numbers = self.journal_id.sequence_id.remaining_numbers
            remaining_days = self.journal_id.sequence_id.remaining_days
            date_range = self.env['ir.sequence.date_range'].search([
                ('sequence_id', '=', self.journal_id.sequence_id.id),
                ('active_resolution', '=', True)])
            today = datetime.strptime(str(datetime.now(timezone(self.env.user.tz)).date()), '%Y-%m-%d')

            if date_range:
                date_range.ensure_one()
                date_to = datetime.strptime(str(date_range.date_to), '%Y-%m-%d')
                days = (date_to - today).days
                numbers = date_range.number_to - date_range.number_next_actual

                if numbers < remaining_numbers or days < remaining_days:
                    warn_remaining = True
            else:
                warn_inactive_resolution = True

        self.warn_inactive_resolution = warn_inactive_resolution
        self.warn_remaining = warn_remaining
        self.einv_available_days = days
        self.einv_available_numbers = numbers

    warn_remaining = fields.Boolean(string="Warn About Remainings?", compute="_get_warn_resolution", store=False)
    warn_inactive_resolution = fields.Boolean(string="Warn About Inactive Resolution?", compute="_get_warn_resolution", store=False)
    einv_available_numbers = fields.Integer(string="Números disponibles", compute="_get_warn_resolution", store=False)
    einv_available_days = fields.Integer(string="Días disponibles", compute="_get_warn_resolution", store=False)

