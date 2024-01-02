# -*- coding: utf-8 -*-
# Copyright 2021 Diego Carvajal <Github@diegoivanc>

from validators import url
from . global_functions import get_pkcs12
from . import global_functions
from odoo import api, models, fields, _
from odoo.exceptions import ValidationError
from requests import post, exceptions
from lxml import etree

import ssl
ssl._create_default_https_context = ssl._create_unverified_context


class ResCompany(models.Model):
    _inherit = "res.company"

    epayroll_enabled = fields.Boolean(string='E-Payroll Enabled')
    profile_execution_payroll_id = fields.Selection([('1', 'Production'),
                                             ('2', 'Test')], 'Destination Environment of Document', default='2', required=True)
    payroll_test_set_id = fields.Char(string='Test Set Id')
    payroll_software_id = fields.Char(string='Software Id')
    payroll_software_pin = fields.Char(string='Software PIN')
    payroll_certificate_filename = fields.Char(string='Certificate Filename')
    payroll_certificate_file = fields.Binary(string='Certificate File')
    payroll_certificate_password = fields.Char(string='Certificate Password')
    payroll_signature_policy_url = fields.Char(string='Signature Policy Url')
    payroll_signature_policy_description = fields.Char(string='Signature Policy Description')
    payroll_signature_policy_filename = fields.Char(string='Signature Policy Filename')
    payroll_signature_policy_file = fields.Binary(string='Signature Policy File')
    payroll_files_path = fields.Char(string='Files Path')
    payroll_get_numbering_range_response = fields.Text(string='GetNumberingRange Response')
    payroll_report_template = fields.Many2one(
        string='Report Template',
        comodel_name='ir.actions.report')
    epayroll_email = fields.Char(
        string='E-invoice Email From',
        help="Enter the e-invoice sender's email.")
    out_nomina_sent = fields.Integer()
    nit_e_payroll = fields.Integer()
    dv_e_payroll = fields.Integer()
    departamento = fields.Char()
    municipio = fields.Char()

    @api.onchange('payroll_signature_policy_url')
    def onchange_signature_policy_url(self):
        if not url(self.payroll_signature_policy_url):
            raise ValidationError(_('Invalid URL.'))

    def write(self, vals):
        rec = super(ResCompany, self).write(vals)
        if self.payroll_certificate_file and self.payroll_certificate_password:
            get_pkcs12(self.payroll_certificate_file, self.payroll_certificate_password)

        return rec


    def _get_GetNumberingRange_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.payroll_certificate_file,
            self.payroll_certificate_password)

        #xml_soap_values['accountCode'] = self.partner_id.identification_document
        #xml_soap_values['accountCodeT'] = self.partner_id.identification_document
        xml_soap_values['softwareCode'] = self.payroll_software_id

        return xml_soap_values

    def action_GetNumberingRangePayroll(self):
        msg1 = _("Unknown Error,\nStatus Code: %s,\nReason: %s.")
        msg2 = _("Unknown Error: %s\n.")
        wsdl = 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc?wsdl'
        s = "http://www.w3.org/2003/05/soap-envelope"

        GetNumberingRange_values = self._get_GetNumberingRange_values()
        GetNumberingRange_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetNumberingRange_values, 'GetNumberingRange'),
            GetNumberingRange_values['Id'],
            self.payroll_certificate_file,
            self.payroll_certificate_password)

        try:
            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature))

            if response.status_code == 200:
                root = etree.fromstring(response.text)
                response = ''

                for element in root.iter("{%s}Body" % s):
                    response = etree.tostring(element, pretty_print=True)

                if response == '':
                    response = etree.tostring(root, pretty_print=True)

                self.write({'get_numbering_range_response': response})
            else:
                raise ValidationError(msg1 % (response.status_code, response.reason))

        except exceptions.RequestException as e:
            raise ValidationError(msg2 % (e))

        return True
