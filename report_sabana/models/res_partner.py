# -*- coding: utf-8 -*-
from odoo import models,fields,api,_

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    
    payment_mean_code_id = fields.Many2one('account.payment.mean.code',
		string='Mean of Payment',
		copy=False)