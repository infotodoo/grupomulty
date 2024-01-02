
from odoo import models, fields, api

class SaleOrderAdionalFreight(models.Model):
    _name = 'sale.order.aditional.freight'
    _description = 'Fletes'

    name =  fields.Char(string="Nombre")
