# -*- coding: utf-8 -*-

from odoo import api, models, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_loyalty_points = fields.Float(compute='compute_partner_loyalty_points', string='Sale Loyalty Points', help='The loyalty points the user won as part of a Loyalty Program')
    sale_loyalty_points_history = fields.One2many('sale.loyalty.points.history', 'partner_id', string='Loyalty History')

    @api.depends('sale_loyalty_points_history')
    def compute_partner_loyalty_points(self):
        for partner in self:
            partner.sale_loyalty_points = 0.00
            if partner.sale_loyalty_points_history:
                partner.sale_loyalty_points = sum(partner.sale_loyalty_points_history.mapped('points'))

    def get_loyalty_points_history(self):
        self.ensure_one()
        points_history = self.env['sale.loyalty.points.history'].search([('partner_id', '=', self.id), ('state', '=', 'confirmed')])
        return points_history

    def get_portal_pdf_url(self, suffix=None, report_type=None, download=None):
        self.ensure_one()
        url = '/my/loyalty/history/%s?%s%s' % (
            self.id,
            'report_type=%s' % report_type if report_type else '',
            '&download=true' if download else ''
        )
        return url

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s - Loyalty Points Report' % (self.name)

    def action_partner_loyalty_points_history(self):
        self.ensure_one()
        if self.sale_loyalty_points_history:
            return {
                'name': _('Partner Loyalty Points History'),
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'sale.loyalty.points.history',
                'domain': [('id', 'in', self.sale_loyalty_points_history.ids)]
            }
