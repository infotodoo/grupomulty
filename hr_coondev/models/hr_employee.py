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

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Empleados'

    eps_id = fields.Many2one('res.partner', string="EPS")
    afp_id = fields.Many2one('res.partner', string="Fondo de Pensiones")
    afc_id = fields.Many2one('res.partner', string="Fondo de Cesantías")
    arl_id = fields.Many2one('res.partner', string="Aseguradora de Riesgos Laborales")
    compensation_box = fields.Many2one('res.partner', string="Caja de compensación")
    risk_classes_type = fields.Selection([('risk1','Clase de Riesgo 1'),
    	('risk2','Clase de Riesgo 2'),
    	('risk3','Clase de Riesgo 3'),
    	('risk4','Clase de Riesgo 4'),
    	('risk5','Clase de Riesgo 5')], string="ARL-Clases de Riesgos")

 