# -*- coding: utf-8 -*-
# Copyright 2021 Diego Carvajal <Github@diegoivanc>


import sys
import importlib
importlib.reload(sys)
import base64
import re
import zipfile

#sys.setdefaultencoding('utf8')
#from StringIO import StringIO
from io import StringIO ## for Python 3
from datetime import datetime, timedelta
from base64 import b64encode, b64decode
from zipfile import ZipFile
from . import global_functions
from pytz import timezone
from requests import post, exceptions
from lxml import etree

from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, UserError
from odoo.http import request

from io import StringIO ## for Python 3
from io import BytesIO

import logging
_logger = logging.getLogger(__name__)

import ssl

ssl._create_default_https_context = ssl._create_unverified_context


DIAN = {'wsdl-hab': 'https://vpfe-hab.dian.gov.co/WcfDianCustomerServices.svc?wsdl',
        'wsdl': 'https://vpfe.dian.gov.co/WcfDianCustomerServices.svc?wsdl',
        'catalogo-hab': 'https://catalogo-vpfe-hab.dian.gov.co/Document/FindDocument?documentKey={}&partitionKey={}&emissionDate={}',
        'catalogo': 'https://catalogo-vpfe.dian.gov.co/Document/FindDocument?documentKey={}&partitionKey={}&emissionDate={}'}

class AccountInvoiceDianDocument(models.Model):
    _inherit = "account.invoice.dian.document"

    def _get_support_values(self):
        xml_values = self._get_xml_suppplier_values(False)
        billing_reference = self.invoice_id._get_billing_reference()
        if billing_reference:
            xml_values['CustomizationID'] = '20'
            self.invoice_id.operation_type = '20'
        xml_values['CustomizationID'] = self.invoice_id.operation_type_supplier
        active_dian_resolution = self.invoice_id._get_active_dian_resolution()
        xml_values['InvoiceControl'] = active_dian_resolution
        xml_values['InvoiceTypeCode'] = self.invoice_id.invoice_type_code
        xml_values['InvoiceLines'] = self.invoice_id._get_invoice_lines()
        xml_values['BillingReference'] = billing_reference
        xml_values['DiscrepancyReferenceID'] = billing_reference['ID']
        xml_values['DiscrepancyResponseCode'] = self.invoice_id.discrepancy_response_code_id.code
        xml_values['DiscrepancyDescription'] = self.invoice_id.discrepancy_response_code_id.name

        return xml_values

    def support_document(self):
        accepted_xml_without_signature = global_functions.get_template_xml(self._get_support_values(), 'SupportDocument')
        accepted_xml_with_signature = global_functions.get_xml_with_signature(accepted_xml_without_signature, self.company_id.signature_policy_url, self.company_id.signature_policy_description, self.company_id.certificate_file, self.company_id.certificate_password)
        if not self.xml_filename or not self.zipped_filename:
            self._set_filenames()
        self.write({'exp_accepted_file': b64encode(self._get_acp_zipped_file(accepted_xml_with_signature)).decode("utf-8", "ignore")})
        self.action_sent_accepted_file(self.exp_accepted_file)
        self.action_set_files()
        self.action_sent_zipped_file()

    def support_document_refund(self):
        accepted_xml_without_signature = global_functions.get_template_xml(self._get_support_values(), 'SupportDocumentCredit')
        accepted_xml_with_signature = global_functions.get_xml_with_signature(accepted_xml_without_signature, self.company_id.signature_policy_url, self.company_id.signature_policy_description, self.company_id.certificate_file, self.company_id.certificate_password)
        if not self.xml_filename or not self.zipped_filename:
            self._set_filenames()
        self.write({'exp_accepted_file': b64encode(self._get_acp_zipped_file(accepted_xml_with_signature)).decode("utf-8", "ignore")})
        self.action_sent_accepted_file(self.exp_accepted_file)
        self.action_set_files()
        self.action_sent_zipped_file()