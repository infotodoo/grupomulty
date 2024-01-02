# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import MissingError, UserError, ValidationError, AccessError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def _move_serials(self, lot_ids, location_id, location_dest_id):
        for item in self:
            movable_confirmed_rental_lines = self.filtered(lambda sol: sol.is_rental and sol.state in ['sale', 'done'] and sol.product_id.type in ["product", "consu"])
            movable_confirmed_rental_lines.mapped('company_id').filtered(lambda company: not company.rental_loc_id)._create_rental_location()
            for sol in movable_confirmed_rental_lines:
                rented_location = sol.company_id.rental_loc_id
                if rented_location == location_id:
                    location_dest_id = item.order_id.warehouse_id.rental_stock_loc_id
            super(SaleOrderLine, item)._move_serials(lot_ids, location_id, location_dest_id)