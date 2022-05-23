# -*- coding: utf-8 -*-

from odoo import models, _
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def unlink(self):
        redeem_point_product = self.env.ref('sale_loyalty.sale_loyalty_product_redeem')
        if self == redeem_point_product:
            raise UserError(_("You can not delete this product as it is using as redeem points product in sale order !"))
        return super(ProductProduct, self).unlink()
