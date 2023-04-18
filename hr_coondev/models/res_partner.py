#Luis Felipe Paternina
#
#Ingeniero de Sistemas
#
# lfpaternina93@gmail.com
#
# Cel: +573215062353
#
# Bogotá,Colombia
#
#################################################################################################################


from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    _description = 'Contactos'

    is_eps = fields.Boolean(string="Es EPS")
    is_afp = fields.Boolean(string="Es Fondo de Pensiones")
    is_afc = fields.Boolean(string="Es Fondo de Cesantías")
    is_arl = fields.Boolean(string="Es Aseguradora de Riesgos Laborales")
    is_compensation_box = fields.Boolean(string="Es Caja de compensación")
    

 