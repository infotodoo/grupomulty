# -*- coding: utf-8 -*-
# Copyright 2021 Diego Carvajal <Github@diegoivanc>


from odoo import api, models, fields, _
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
	_inherit = "stock.warehouse"

	rental_stock_loc_id = fields.Many2one('stock.location', 'ubicacion de Renta', check_company=True)