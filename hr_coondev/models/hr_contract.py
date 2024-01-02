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

class HrContract(models.Model):
    _inherit = 'hr.contract'
    funeral_contract = fields.Float(string='Plan excequial')
    insurance_contract = fields.Float(string='Seguros')
    loan_contract = fields.Float(string='Prestamos')
    bearing_contract = fields.Float(string='Auxilios')
    discount_contract = fields.Float(string='Bonificacion por cargo')
    interest_contract = fields.Float(string='Intereses')
    embargos_contract = fields.Float(string='Embargos')
