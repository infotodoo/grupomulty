
from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    partner_esp_id = fields.Many2one('hr.employee',string="Especialista")
    pronostic_type = fields.Selection([('better','Mejor Caso'),('commitment','Compromiso')],string="Pronostico")
    

    