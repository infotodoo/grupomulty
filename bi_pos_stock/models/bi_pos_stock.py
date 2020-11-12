# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import Warning
import random
from odoo.tools import float_is_zero
from datetime import date, datetime


class pos_config(models.Model):
	_inherit = 'pos.config'

	def _get_default_location(self):
		return self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1).lot_stock_id
	
	pos_display_stock = fields.Boolean(string='Display Stock in POS')
	pos_stock_type = fields.Selection([('onhand', 'Qty on Hand'), ('incoming', 'Incoming Qty'), ('outgoing', 'Outgoing Qty'), ('available', 'Qty Available')], string='Stock Type', help='Seller can display Different stock type in POS.')
	pos_allow_order = fields.Boolean(string='Allow POS Order When Product is Out of Stock')
	pos_deny_order = fields.Char(string='Deny POS Order When Product Qty is goes down to')   
	
	show_stock_location = fields.Selection([
		('all', 'All Warehouse'),
		('specific', 'Current Session Warehouse'),
		], string='Show Stock Of', default='all')

	stock_location_id = fields.Many2one(
		'stock.location', string='Stock Location',
		domain=[('usage', '=', 'internal')], required=True, default=_get_default_location)

		
class pos_order(models.Model):
	_inherit = 'pos.order'

	location_id = fields.Many2one(
		comodel_name='stock.location',
		related='config_id.stock_location_id',
		string="Location", store=True,
		readonly=True,
	)

	def create_picking(self):
		"""Create a picking for each order and validate it."""
		Picking = self.env['stock.picking']
		# If no email is set on the user, the picking creation and validation will fail be cause of
		# the 'Unable to log message, please configure the sender's email address.' error.
		# We disable the tracking in this case.
		if not self.env.user.partner_id.email:
			Picking = Picking.with_context(tracking_disable=True)
		Move = self.env['stock.move']
		StockWarehouse = self.env['stock.warehouse']
		for order in self:
			if not order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
				continue
			address = order.partner_id.address_get(['delivery']) or {}
			picking_type = order.picking_type_id
			return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
			order_picking = Picking
			return_picking = Picking
			moves = Move
			location_id = order.location_id.id
			if order.partner_id:
				destination_id = order.partner_id.property_stock_customer.id
			else:
				if (not picking_type) or (not picking_type.default_location_dest_id):
					customerloc, supplierloc = StockWarehouse._get_partner_locations()
					destination_id = customerloc.id
				else:
					destination_id = picking_type.default_location_dest_id.id

			if picking_type:
				message = _("This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
				picking_vals = {
					'origin': order.name,
					'partner_id': address.get('delivery', False),
					'user_id': False,
					'date_done': order.date_order,
					'picking_type_id': picking_type.id,
					'company_id': order.company_id.id,
					'move_type': 'direct',
					'note': order.note or "",
					'location_id': location_id,
					'location_dest_id': destination_id,
				}
				pos_qty = any([x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
				if pos_qty:
					order_picking = Picking.create(picking_vals.copy())
					if self.env.user.partner_id.email:
						order_picking.message_post(body=message)
					else:
						order_picking.sudo().message_post(body=message)
				neg_qty = any([x.qty < 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
				if neg_qty:
					return_vals = picking_vals.copy()
					return_vals.update({
						'location_id': destination_id,
						'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
						'picking_type_id': return_pick_type.id
					})
					return_picking = Picking.create(return_vals)
					if self.env.user.partner_id.email:
						return_picking.message_post(body=message)
					else:
						return_picking.message_post(body=message)

			for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
				moves |= Move.create({
					'name': line.name,
					'product_uom': line.product_id.uom_id.id,
					'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
					'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
					'product_id': line.product_id.id,
					'product_uom_qty': abs(line.qty),
					'state': 'draft',
					'location_id': location_id if line.qty >= 0 else destination_id,
					'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
				})

			# prefer associating the regular order picking, not the return
			order.write({'picking_id': order_picking.id or return_picking.id})

			if return_picking:
				order._force_picking_done(return_picking)
			if order_picking:
				order._force_picking_done(order_picking)

			# when the pos.config has no picking_type_id set only the moves will be created
			if moves and not return_picking and not order_picking:
				moves._action_assign()
				moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()

		return True


class stock_quant(models.Model):
	_inherit = 'stock.quant'

	def get_stock_location_qty(self, location):
		res = {}
		product_ids = self.env['product.product'].search([])
		for product in product_ids:
			quants = self.env['stock.quant'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
			if len(quants) > 1:
				quantity = 0.0
				for quant in quants:
					quantity += quant.quantity
				res.update({product.id : quantity})
			else:
				res.update({product.id : quants.quantity})
		return [res]

	def get_products_stock_location_qty(self, location,products):
		res = {}
		product_ids = self.env['product.product'].browse(products)
		for product in product_ids:
			quants = self.env['stock.quant'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
			if len(quants) > 1:
				quantity = 0.0
				for quant in quants:
					quantity += quant.quantity
				res.update({product.id : quantity})
			else:
				res.update({product.id : quants.quantity})
		return [res]

	def get_single_product(self,product, location):
		res = []
		pro = self.env['product.product'].browse(product)
		quants = self.env['stock.quant'].search([('product_id', '=', pro.id),('location_id', '=', location['id'])])
		if len(quants) > 1:
			quantity = 0.0
			for quant in quants:
				quantity += quant.quantity
			res.append([pro.id, quantity])
		else:
			res.append([pro.id, quants.quantity])
		return res


class product(models.Model):
	_inherit = 'product.product'
	
	available_quantity = fields.Float('Available Quantity')

	def get_stock_location_avail_qty(self, location):
		res = {}
		product_ids = self.env['product.product'].search([])
		for product in product_ids:
			quants = self.env['stock.quant'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
			outgoing = self.env['stock.move'].search([('product_id', '=', product.id),('location_id', '=', location['id'])])
			incoming = self.env['stock.move'].search([('product_id', '=', product.id),('location_dest_id', '=', location['id'])])
			qty=0.0
			product_qty = 0.0
			incoming_qty = 0.0
			if len(quants) > 1:
				for quant in quants:
					qty += quant.quantity

				if len(outgoing) > 0:
					for quant in outgoing:
						if quant.state not in ['done']:
							product_qty += quant.product_qty

				if len(incoming) > 0:
					for quant in incoming:
						if quant.state not in ['done']:
							incoming_qty += quant.product_qty
					product.available_quantity = qty-product_qty + incoming_qty
					res.update({product.id : qty-product_qty + incoming_qty})
			else:
				if not quants:
					if len(outgoing) > 0:
						for quant in outgoing:
							if quant.state not in ['done']:
								product_qty += quant.product_qty

					if len(incoming) > 0:
						for quant in incoming:
							if quant.state not in ['done']:
								incoming_qty += quant.product_qty
					product.available_quantity = qty-product_qty + incoming_qty
					res.update({product.id : qty-product_qty + incoming_qty})
				else:
					if len(outgoing) > 0:
						for quant in outgoing:
							if quant.state not in ['done']:
								product_qty += quant.product_qty

					if len(incoming) > 0:
						for quant in incoming:
							if quant.state not in ['done']:
								incoming_qty += quant.product_qty
					product.available_quantity = quants.quantity - product_qty + incoming_qty
					res.update({product.id : quants.quantity - product_qty + incoming_qty})
		return [res]
	

