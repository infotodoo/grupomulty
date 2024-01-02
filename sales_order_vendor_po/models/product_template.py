# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    num_part = fields.Char(
        'Número de Parte',
        copy=False,
        index=True)
    

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('num_part', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', operator, name), ('num_part', operator, name), ('default_code', operator, name),]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.depends('product_tmpl_id')
    def _compute_num_part(self):
        for product in self:
            product.num_part = product.product_tmpl_id.num_part

    num_part = fields.Char(
        string='Número de Parte')
