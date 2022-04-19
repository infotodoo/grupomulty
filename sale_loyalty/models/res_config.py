# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    loyalty_id = fields.Many2one(related='company_id.loyalty_id', string='Loyalty Program', domain="[('company_id', '=', company_id)]", readonly=False, help='Set Loyalty Program on Sale Order')
