# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LoyaltyProgram(models.Model):
    _name = 'sale.loyalty.program'
    _description = 'Sale Loyalty Program'

    name = fields.Char(string='Loyalty Program Name', index=True, required=True, help="An internal identification for the loyalty program configuration")
    pp_currency = fields.Float(string='Points per currency', help="How many loyalty points are given to the customer by sold currency")
    pp_product = fields.Float(string='Points per product', help="How many loyalty points are given to the customer by product sold")
    pp_order = fields.Float(string='Points per order', help="How many loyalty points are given to the customer for each sale or order")
    rounding = fields.Float(string='Points Rounding', default=1, help="The loyalty point amounts are rounded to multiples of this value.")
    rule_ids = fields.One2many('sale.loyalty.rule', 'loyalty_program_id', string='Rules')
    reward_ids = fields.One2many('sale.loyalty.reward', 'loyalty_program_id', string='Rewards')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)


class LoyaltyRule(models.Model):
    _name = 'sale.loyalty.rule'
    _description = 'Sale Loyalty Rule'

    name = fields.Char(index=True, required=True, help="An internal identification for this loyalty program rule")
    loyalty_program_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', help='The Loyalty Program this exception belongs to')
    rule_type = fields.Selection([('product', 'Product'), ('category', 'Category')], required=True, default='product', help='Does this rule affects products, or a category of products ?')
    product_id = fields.Many2one('product.product', string='Target Product', help='The product affected by the rule')
    category_id = fields.Many2one('product.category', string='Target Category', help='The category affected by the rule')
    cumulative = fields.Boolean(help='The points won from this rule will be won in addition to other rules')
    pp_product = fields.Float(string='Points Per Product', help='How many points the product will earn per product ordered')
    pp_currency = fields.Float(string='Points Per Currency', help='How many points the product will earn per value sold')
    company_id = fields.Many2one(related='loyalty_program_id.company_id', string='Company', store=True, readonly=True, index=True)


class LoyaltyReward(models.Model):
    _name = 'sale.loyalty.reward'
    _description = 'Sale Loyalty Reward'

    name = fields.Char(index=True, required=True, help='An internal identification for this loyalty reward')
    loyalty_program_id = fields.Many2one('sale.loyalty.program', string='Loyalty Program', help='The Loyalty Program this reward belongs to')
    minimum_points = fields.Float(help='The minimum amount of points the customer must have to qualify for this reward')
    reward_type = fields.Selection([('gift', 'Gift'), ('discount', 'Discount')], required=True, help='The type of the reward')
    gift_product_id = fields.Many2one('product.product', string='Gift Product', help='The product given as a reward')
    point_cost = fields.Float(help='The cost of the reward')
    discount_product_id = fields.Many2one('product.product', string='Discount Product', help='The product used to apply discounts')
    discount = fields.Float(string="Discount(%)", help='The discount percentage')
    company_id = fields.Many2one(related='loyalty_program_id.company_id', string='Company', store=True, readonly=True, index=True)

    @api.constrains('reward_type', 'gift_product_id')
    def _check_gift_product(self):
        if self.filtered(lambda reward: reward.reward_type == 'gift' and not reward.gift_product_id):
            raise ValidationError(_('The gift product field is mandatory for gift rewards'))

    @api.constrains('reward_type', 'discount_product_id')
    def _check_discount_product(self):
        if self.filtered(lambda reward: reward.reward_type == 'discount' and not reward.discount_product_id):
            raise ValidationError(_('The discount product field is mandatory for discount rewards'))

    @api.onchange('reward_type')
    def onchange_reward_type(self):
        if self.reward_type:
            if self.reward_type == 'discount':
                self.discount_product_id = self.env.ref('sale_loyalty.sale_loyalty_product_discount').id


class SaleLoyaltyPointsHistory(models.Model):
    _name = 'sale.loyalty.points.history'
    _description = 'Sale Loyalty Points History'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', required=True)
    date = fields.Datetime(required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    point_type = fields.Selection([('earn', 'Earned'), ('redeem', 'Redeemed')], string='Type', required=True, default='earn')
    points = fields.Float(required=True)
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default='draft', required=True)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            return {'domain': {'sale_order_id': [('partner_id', '=', self.partner_id.id)]}}

    def action_cancel(self):
        for history in self:
            history.write({'state': 'cancelled'})

    def action_draft(self):
        for history in self:
            history.write({'state': 'draft'})
