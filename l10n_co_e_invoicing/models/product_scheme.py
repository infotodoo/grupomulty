# -*- coding: utf-8 -*-

from odoo import models, fields


class ProductScheme(models.Model):
    _name = 'product.scheme'

    code = fields.Char(string='schemeID')
    name = fields.Char(string='schemeName')
    scheme_agency_id = fields.Char(string='schemeAgencyID')
