# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection(
    selection=[
        ('draft', 'Quotation'),
        ('draft_ok', 'Aprobada'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ],
    )
    approval_margin = fields.Float(string="Margen de aprobación")
    check_margin = fields.Boolean(string="Validar margen", compute="_compute_check_approval_margin")
    total_percentage_margin = fields.Float(string="% total del margen")


    @api.onchange('order_line')
    def _onchnage_margin(self):
        if self.margin_real:
            self.total_percentage_margin = self.margin_percent_real * 100
        else:
            self.total_percentage_margin = 0.0


    def write_state(self):
        self.write({'state': 'draft_ok'})
        return True


    @api.onchange('order_line')
    def calculated_approvals_margin(self):
        approval = []
        approval_obj = self.env['sale.approvals.settings'].search([('approval_quantity', '>', 0)], limit=1)
        if approval_obj:
            self.approval_margin = approval_obj.approval_quantity
        else:
            print("Objeto vacio")


    @api.depends('approval_margin')
    def _compute_check_approval_margin(self):
        for record in self:
            if record.approval_margin and (record.state in ('draft','sent')):
                if record.approval_margin > record.total_percentage_margin:
                    record.check_margin = True
                else:
                    record.check_margin = False
            else:
                record.check_margin = False

