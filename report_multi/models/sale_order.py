# -*- coding: utf-8 -*-

from odoo import models, fields
from functools import partial
from itertools import groupby
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare

class SaleOrderMulti(models.Model):

    _inherit = "sale.order"
    _description = "Sales Order"
    zone = fields.Many2one('res.partner.zone', string="Zona", related="partner_id.zone")


    