# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#                                                                             #
# Part of Odoo. See LICENSE file for full copyright and licensing details.    #
#                                                                             #
#                                                                             #
#                                                                             #
# Co-Authors    Odoo LoCo                                                     #
#               Localización funcional de Odoo para Colombia                  #
#                                                                             #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################


from odoo import models, fields, api, osv, _
import logging
_logger = logging.getLogger(__name__)
import json


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create_from_ui(self, partner):

        if('document_type_id' in partner):
            document_type_id = int(partner['document_type_id'])
            del partner['document_type_id']
            partner['document_type_id'] = document_type_id

        if('person_type' in partner):
            person_type = partner['person_type']
            del partner['person_type']
            partner['person_type'] = person_type

        partner_id = partner.pop('id', False)
        if partner_id:  # Modifying existing partner
            self.browse(partner_id).write(partner)
        else:
            partner['lang'] = self.env.user.lang
            partner_id = self.create(partner).id

        return partner_id


    def get_document_type_id(self):
        result = []
        for item in self.env['res.partner'].fields_get(self)['document_type_id']:
            result.append({'id': item[0], 'name': item[1]})
        return result


    def get_person_type(self):
        result = []
        for item in self.env['res.partner'].fields_get(self)['person_type']['selection']:
            result.append({'id': item[0], 'name': item[1]})
        return result

class AccountInvoice(models.Model):
    _inherit = "account.move"

    @api.model
    def _default_payment_mean(self):
        _logger.info('entro a default')
        id_model = self.env['account.payment.mean'].search([], limit=1)
        return id_model

    payment_mean_id = fields.Many2one(
		comodel_name='account.payment.mean',
		string='Payment Method',
		default=_default_payment_mean)

