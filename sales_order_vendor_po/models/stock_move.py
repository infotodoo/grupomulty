# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_procurement_values(self):
        res = super(StockMove, self)._prepare_procurement_values()
        if self.sale_line_id and self.sale_line_id.custom_vendor_id:
            res.update({
                'supplier_id': self.sale_line_id.custom_vendor_id,
            })
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
