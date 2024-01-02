# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleApprovalsSettins(models.Model):
    _name = "sale.approvals.settings"
    _description = "Configuración de aprobaciones"

    name = fields.Char(string="Nombre")
    approval_quantity = fields.Float(string="Porcentage a aprobar")
    letter = fields.Char(default="a")
    percentage = fields.Float(string="%", related="approval_quantity")


    _sql_constraints = [
        ('letter_uniq', 'unique (letter)','Solo se puede crear un registro en este modelo!')
    ]

    @api.constrains('approval_quantity')
    def _validate_approval_quantity(self):
        for record in self:
            if record.approval_quantity > 100.0:
                raise ValidationError("El porcentage no puede ser mayor a 100%")