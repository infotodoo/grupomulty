from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ProjectTask(models.Model):
    _inherit = 'project.task'

    approval_id = fields.Many2one(
        'res.users',
        string="Aprobador")
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="Centro de Costo")
    way_to_pay = fields.Char(
        string="Forma de pago")
