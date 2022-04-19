# -*- coding: utf-8 -*-

from odoo import fields, models, _
from odoo.exceptions import UserError


class PointSelectionWizard(models.TransientModel):
    _name = 'point.selection.wizard'
    _description = 'Point Selection Wizard'

    points = fields.Integer(required=True)
    order_id = fields.Many2one('sale.order', 'Sale Order')
    loyalty_id = fields.Many2one('sale.loyalty.program', 'Sale Loyalty Program')

    def action_point_redeem(self):
        if self.points <= 0:
            raise UserError(_("Points must be greater than zero !"))
        product = self.env.ref('sale_loyalty.sale_loyalty_product_redeem')
        total_point_cost = round(self.order_id.amount_total / product.lst_price) + self.order_id.points_spent
        if self.points:
            if self.points > total_point_cost:
                raise UserError(_("You can redeem max upto %s points !" % str(int(round(self.order_id.amount_total / product.lst_price)))))
            total_point_cost = self.points

        if total_point_cost + (self.order_id.points_spent * -1) > self.order_id.partner_id.sale_loyalty_points:
            raise UserError(_("You can redeem max upto %s points !" % str(int(self.order_id.partner_id.sale_loyalty_points + self.order_id.points_spent))))
        else:
            price = -product.lst_price
            if -(price * total_point_cost) > self.order_id.amount_total:
                total_point_cost -= 1
            exist_order_line = self.order_id.order_line.filtered(lambda x: x.product_id == product and x.reward_line and x.reward_type == 'resale')
            if exist_order_line:
                exist_order_line[0].write({
                    'product_uom_qty': exist_order_line[0].product_uom_qty + total_point_cost,
                    'product_uom': product.uom_id.id,
                    'price_unit': price,
                    'spent_point': exist_order_line[0].spent_point + total_point_cost,
                })
            else:
                self.env['sale.order.line'].create({
                    'product_id': product.id,
                    'product_uom_qty': total_point_cost,
                    'product_uom': product.uom_id.id,
                    'price_unit': price,
                    'spent_point': total_point_cost,
                    'reward_line': True,
                    'reward_type': 'resale',
                    'order_id': self.order_id.id})
            self.order_id.compute_points_spent()
        return {'type': 'ir.actions.act_window_close'}
