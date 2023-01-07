# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# Copyright 2019 Diego Carvajal <Github@diegoivanc>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys
import importlib
importlib.reload(sys)
import base64
import re

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
    _name = "account.invoice.dian.document"
    _inherit = ['mail.thread']

    state = fields.Selection([('draft', 'Draft'),
                              ('sent', 'Sent'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel')], string='State', readonly=True, default='draft', tracking=True)
    invoice_id = fields.Many2one('account.move', string='Invoice')
    company_id = fields.Many2one('res.company', string='Company')
    invoice_url = fields.Char(string='Invoice Url', tracking=True)
    cufe_cude_uncoded = fields.Char(string='CUFE/CUDE Uncoded', tracking=True)
    cufe_cude = fields.Char(string='CUFE/CUDE', tracking=True)
    origin_cufe_cude = fields.Char(string='CUFE/CUDE original')
    software_security_code_uncoded = fields.Char(string='SoftwareSecurityCode Uncoded', tracking=True)
    software_security_code = fields.Char(string='SoftwareSecurityCode')
    xml_filename = fields.Char(string='XML Filename')
    xml_file = fields.Binary(string='XML File')
    zipped_filename = fields.Char(string='Zipped Filename')
    zipped_file = fields.Binary(string='Zipped File')
    zip_key = fields.Char(string='ZipKey')
    mail_sent = fields.Boolean(string='Mail Sent?', tracking=True)
    ar_xml_filename = fields.Char(string='ApplicationResponse XML Filename')
    ar_xml_file = fields.Binary(string='ApplicationResponse XML File', tracking=True)
    get_status_zip_status_code = fields.Selection([('00', 'Procesado Correctamente'),
                                                   ('66', 'NSU no encontrado'),
                                                   ('90', 'TrackId no encontrado'),
                                                   ('99', 'Validaciones contienen errores en campos mandatorios'),
                                                   ('other', 'Other')], string='StatusCode', default=False, tracking=True)
    get_status_zip_response = fields.Text(string='Response', tracking=True)
    qr_image = fields.Binary("QR Code", compute='_generate_qr_code')
    dian_document_line_ids = fields.One2many('account.invoice.dian.document.line', 'dian_document_id', string='DIAN Document Lines')
    profile_execution_id = fields.Selection(string='Destination Environment of Document', related='company_id.profile_execution_id', store=False)
    type_account = fields.Selection([('debit', 'Debit Note'),
                                     ('credit', 'Credit Note'),
                                     ('invoice', 'Invoice')])

    def state_to_cancel(self):
        if self.state == 'done' or self.get_status_zip_status_code == '00':
            raise ValidationError(_('No puede cancelar un documento DIAN autorizado'))
        self.state == 'cancel'

    def go_to_dian_document(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dian Document',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'current'}

    def _generate_qr_code(self):
        einvoicing_taxes = self.invoice_id._get_einvoicing_taxes()
        try:
            ValImp1 = einvoicing_taxes['TaxesTotal']['01']['total']
        except:
            ValImp1 = 0
        try:
            ValImp2 = einvoicing_taxes['TaxesTotal']['04']['total']
        except:
            ValImp2 = 0
        try:
            ValImp3 = einvoicing_taxes['TaxesTotal']['03']['total']
        except:
            ValImp3 = 0

        ValFac = self.invoice_id.amount_untaxed
        ValOtroIm = ValImp2 - ValImp3
        ValTolFac = ValFac + ValImp1 + ValImp2 + ValImp3
        date_format = str(self.invoice_id.create_date)[0:19]
        create_date = datetime.strptime(date_format, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        nit_fac = self.company_id.partner_id.identification_document
        nit_adq = self.invoice_id.partner_id.identification_document
        cufe = self.cufe_cude
        number = self.invoice_id.name

        qr_data = "NumFac: " + number if number else 'NO_VALIDADA'

        qr_data += "\nNitFac: " + nit_fac if nit_fac else ''
        qr_data += "\nNitAdq: " + nit_adq if nit_adq else ''
        qr_data += "\nValFac: " + '{:.2f}'.format(ValFac)
        qr_data += "\nValIva: " + '{:.2f}'.format(ValImp1)
        qr_data += "\nValOtroIm: " + '{:.2f}'.format(ValOtroIm)
        qr_data += "\nValTolFac: " + '{:.2f}'.format(ValTolFac)
        qr_data += "\nCUFE: " + cufe if cufe else ''
        qr_data += "\n\n" + self.invoice_url if self.invoice_url else ''

        self.qr_image = global_functions.get_qr_code(qr_data)


    def _get_GetStatus_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['trackId'] = self.cufe_cude
        _logger.info('trackid')
        _logger.info(self.cufe_cude)

        return xml_soap_values



    def action_GetStatus(self):
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']

        GetStatus_values = self._get_GetStatus_values()
        GetStatus_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetStatus_values, 'GetStatus'),
            GetStatus_values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        response = post(
            wsdl,
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature, encoding="unicode"))

        if response.status_code == 200:
            self._get_status_response(response,send_mail=False)
        else:
            raise ValidationError(response.status_code)

        return True


    def _get_pdf_file(self):
        template = self.env['ir.actions.report'].browse(self.company_id.report_template.id)
        #pdf = self.env.ref('account.move').render_qweb_pdf([self.invoice_id.id])[0]
        if template:
            pdf = template._render_qweb_pdf(self.invoice_id.id)
        else:
            pdf = self.env.ref('account.account_invoices').render_qweb_pdf(self.invoice_id.id)
        pdf_name = re.sub(r'\W+', '', self.invoice_id.name) + '.pdf'

        _logger.info('pdf')
        _logger.info('pdf')
        _logger.info('pdf')
        _logger.info(pdf_name)
        #pdf = self.env['ir.actions.report'].sudo()._run_wkhtmltopdf([self.invoice_id.id], template.report_name)

        return pdf

    def action_send_mail(self):
        msg = _("Your invoice has not been validated")
        template_id = self.env.ref('l10n_co_e_invoicing.email_template_for_einvoice').id
        template = self.env['mail.template'].browse(template_id)

        if not self.invoice_id.name:
            raise UserError(msg)
        
        xml_attachment_file = False
        if self.ar_xml_file and self.xml_file:
            xml_without_signature = global_functions.get_template_xml(self._get_attachment_values(), 'attachment')
            
            xml_attachment_file = self.env['ir.attachment'].create({
                'name': self.invoice_id.name + '-attachment.xml',
                'type': 'binary',
                'datas': b64encode(xml_without_signature.encode()).decode("utf-8", "ignore")})

        xml_attachment = self.env['ir.attachment'].create({
            'name': self.xml_filename,
            'type': 'binary',
            'datas': self.xml_file})
        pdf_attachment = self.env['ir.attachment'].create({
            'name': self.invoice_id.name + '.pdf',
            'type': 'binary',
            'datas': self._get_pdf_file()})

        attach_ids = [xml_attachment.id, pdf_attachment.id]

        if self.invoice_id.invoice_type_code in ('01', '02'):
            template.attachment_ids = [(6, 0, attach_ids)]
        else:
            template.attachment_ids = [(6, 0, attach_ids)]

        template.send_mail(self.invoice_id.id, force_send=True)
        self.write({'mail_sent': True})
        #xml_attachment.unlink()
        #pdf_attachment.unlink()

        if self.invoice_id.invoice_type_code in ('01', '02'):
            #ar_xml_attachment.unlink()
            _logger.info('dasda')

        return True


    def _get_status_response(self, response, send_mail):
        b = "http://schemas.datacontract.org/2004/07/DianResponse"
        c = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
        s = "http://www.w3.org/2003/05/soap-envelope"
        strings = ''
        to_return = True
        status_code = 'other'
        root = etree.fromstring(response.content)
        date_invoice = self.invoice_id.invoice_date

        if not date_invoice:
            date_invoice = fields.Date.today()

        for element in root.iter("{%s}StatusCode" % b):
            if element.text in ('0', '00', '66', '90', '99'):
                if element.text == '00':
                    self.write({'state': 'done'})

                    if self.get_status_zip_status_code != '00':
                        if (self.invoice_id.move_type == "out_invoice"
                            and not self.invoice_id.refund_type):
                            self.company_id.out_invoice_sent += 1
                        elif (self.invoice_id.move_type == "out_refund"
                              and self.invoice_id.refund_type != "debit"):
                            self.company_id.out_refund_sent += 1
                        elif (self.invoice_id.move_type == "out_invoice"
                              and self.invoice_id.refund_type == "debit"):
                            self.company_id.out_refund_sent += 1

                status_code = element.text
        if status_code == '0':
            self.action_GetStatus()

            return True

        if status_code == '00':
            for element in root.iter("{%s}StatusMessage" % b):
                strings = element.text

            for element in root.iter("{%s}XmlBase64Bytes" % b):
                self.write({'ar_xml_file': element.text})

            if not self.mail_sent:
                self.action_send_mail()
            to_return = True
        else:
            if send_mail:
                self.send_failure_email()
            self.send_failure_email()
            to_return = True

        for element in root.iter("{%s}string" % c):
            if strings == '':
                strings = '- ' + element.text
            else:
                strings += '\n\n- ' + element.text

        if strings == '':
            for element in root.iter("{%s}Body" % s):
                strings = etree.tostring(element, pretty_print=True)

            if strings == '':
                strings = etree.tostring(root, pretty_print=True)

        self.write({
            'get_status_zip_status_code': status_code,
            'get_status_zip_response': strings})

        return True

    def send_failure_email(self):
        msg1 = _("The notification group for Einvoice failures is not set.\n" +
                 "You won't be notified if something goes wrong.\n" +
                 "Please go to Settings > Company > Notification Group.")
        subject = _('ALERTA! La Factura %s no fue enviada a la DIAN.') % self.invoice_id.name
        msg_body = _('''Cordial Saludo,<br/><br/>La factura ''' + self.invoice_id.name +
                     ''' del cliente ''' + self.invoice_id.partner_id.name + ''' no pudo ser ''' +
                     '''enviada a la Dian según el protocolo establecido previamente. Por '''
                     '''favor revise el estado de la misma en el menú Documentos Dian e '''
                     '''intente reprocesarla según el procedimiento definido.'''
                     '''<br/>''' + self.company_id.name + '''.''')
        email_ids = self.company_id.notification_group_ids

        if email_ids:
            email_to = ''

            for mail_id in email_ids:
                email_to += mail_id.email.strip() + ','
        else:
            raise UserError(msg1)

        mail_obj = self.env['mail.mail']
        msg_vals = {
            'subject': subject,
            'email_to': email_to,
            'body_html': msg_body}
        msg_id = mail_obj.create(msg_vals)
        msg_id.send()

        return True


    def _set_filenames(self):
        #nnnnnnnnnn: NIT del Facturador Electrónico sin DV, de diez (10) dígitos
        # alineados a la derecha y relleno con ceros a la izquierda.
        if self.company_id.partner_id.identification_document:
            nnnnnnnnnn = self.company_id.partner_id.identification_document.zfill(10)
        else:
            raise ValidationError("The company identification document is not "
                                  "established in the partner.\n\nGo to Contacts > "
                                  "[Your company name] to configure it.")
        #El Código “ppp” es 000 para Software Propio
        ppp = '000'
        #aa: Dos (2) últimos dígitos año calendario
        aa = datetime.now().replace(
            tzinfo=timezone('America/Bogota')).strftime('%y')
        #dddddddd: consecutivo del paquete de archivos comprimidos enviados;
        # de ocho (8) dígitos decimales alineados a la derecha y ajustado a la
        # izquierda con ceros; en el rango:
        #   00000001 <= 99999999
        # Ejemplo de la décima primera factura del Facturador Electrónico con
        # NIT 901138658 con software propio para el año 2019.
        # Regla: el consecutivo se iniciará en “00000001” cada primero de enero.
        out_invoice_sent = self.company_id.out_invoice_sent
        out_refund_sent = self.company_id.out_refund_sent
        in_refund_sent = self.company_id.in_refund_sent
        zip_sent = out_invoice_sent + out_refund_sent + in_refund_sent

        if self.invoice_id.move_type == 'out_invoice' and not self.invoice_id.refund_type:
            xml_filename_prefix = 'fv'
            dddddddd = str(out_invoice_sent + 1).zfill(8)
        elif self.invoice_id.move_type == 'out_refund' and self.invoice_id.refund_type != 'debit':
            xml_filename_prefix = 'nc'
            dddddddd = str(out_refund_sent + 1).zfill(8)
        elif self.invoice_id.move_type == 'out_invoice' and self.invoice_id.refund_type == 'debit':
            xml_filename_prefix = 'nd'
            dddddddd = str(out_refund_sent + 1).zfill(8)


        # elif self.invoice_id.type == 'out_refund':
        #     xml_filename_prefix = 'nc'
        #     dddddddd = str(out_refund_sent + 1).zfill(8)
        # elif self.invoice_id.type == 'in_refund':
        #     xml_filename_prefix = 'nd'
        #     dddddddd = str(in_refund_sent + 1).zfill(8)
        #pendiente
        #arnnnnnnnnnnpppaadddddddd.xml
        #adnnnnnnnnnnpppaadddddddd.xml
        else:
            raise ValidationError("ERROR: TODO")

        zdddddddd = str(zip_sent + 1).zfill(8)
        nnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + dddddddd
        znnnnnnnnnnpppaadddddddd = nnnnnnnnnn + ppp + aa + zdddddddd

        self.write({
            'xml_filename': xml_filename_prefix + nnnnnnnnnnpppaadddddddd + '.xml',
            'zipped_filename': 'z' + znnnnnnnnnnpppaadddddddd + '.zip'})



    def _get_xml_values(self, ClTec):
        msg7 = _('The Incoterm is not defined for this export type invoice')

        active_dian_resolution = self.invoice_id._get_active_dian_resolution()
        einvoicing_taxes = self.invoice_id._get_einvoicing_taxes()
        _logger.info(self.invoice_id.create_date)
        date_format = str(self.invoice_id.create_date)[0:19]
        _logger.info(date_format)
        create_date = datetime.strptime(date_format, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        ID = self.invoice_id.name
        IssueDate = self.invoice_id.invoice_date
        IssueTime = create_date.astimezone(
            timezone('America/Bogota')).strftime('%H:%M:%S-05:00')

        LossRiskResponsibilityCode = self.invoice_id.invoice_incoterm_id.code or ''
        LossRisk = self.invoice_id.invoice_incoterm_id.name or ''
        if self.invoice_id.invoice_type_code == '02':
            if not self.invoice_id.invoice_incoterm_id:
                raise UserError(msg7)
            elif not self.invoice_id.invoice_incoterm_id.name or not self.invoice_id.invoice_incoterm_id.code:
                raise UserError('Incoterm is not properly parameterized')
            else:
                LossRiskResponsibilityCode = self.invoice_id.invoice_incoterm_id.code
                LossRisk = self.invoice_id.invoice_incoterm_id.name

        supplier = self.company_id.partner_id
        customer = self.invoice_id.partner_id
        NitOFE = supplier.identification_document
        NitAdq = customer.identification_document

        ClTec = False
        SoftwarePIN = False
        IdSoftware = self.company_id.software_id

        if self.invoice_id.move_type == 'out_invoice' and not self.invoice_id.refund_type:
            ClTec = active_dian_resolution['technical_key']
        else:
            SoftwarePIN = self.company_id.software_pin

        TipoAmbie = self.company_id.profile_execution_id

        if TipoAmbie == '1':
            QRCodeURL = DIAN['catalogo']
        else:
            QRCodeURL = DIAN['catalogo-hab']

        ValFac = self.invoice_id.amount_untaxed
        try:
            ValImp1 = einvoicing_taxes['TaxesTotal']['01']['total']
        except:
            ValImp1 = 0
        try:
            ValImp2 = einvoicing_taxes['TaxesTotal']['04']['total']
        except:
            ValImp2 = 0
        try:
            ValImp3 = einvoicing_taxes['TaxesTotal']['03']['total']
        except:
            ValImp3 = 0
        TaxInclusiveAmount = ValFac + ValImp1 + ValImp2 + ValImp3
        #El valor a pagar puede verse afectado, por anticipos, y descuentos y
        #cargos a nivel de factura
        PayableAmount = TaxInclusiveAmount
        cufe_cude = global_functions.get_cufe_cude(
            ID,
            IssueDate,
            IssueTime,
            str('{:.2f}'.format(ValFac)),
            '01',
            str('{:.2f}'.format(ValImp1)),
            '04',
            str('{:.2f}'.format(ValImp2)),
            '03',
            str('{:.2f}'.format(ValImp3)),
            str('{:.2f}'.format(TaxInclusiveAmount)),#self.invoice_id.amount_total
            NitOFE,
            NitAdq,
            ClTec,
            SoftwarePIN,
            TipoAmbie)
        software_security_code = global_functions.get_software_security_code(
            IdSoftware,
            self.company_id.software_pin,
            ID)
        partition_key = 'co|' + str(IssueDate).split('-')[2] + '|' + cufe_cude['CUFE/CUDE'][:2]
        emission_date = str(IssueDate).replace('-', '')
        QRCodeURL = QRCodeURL.format(cufe_cude['CUFE/CUDE'], partition_key, emission_date)

        self.write({
            'invoice_url': QRCodeURL,
            'cufe_cude_uncoded': cufe_cude['CUFE/CUDEUncoded'],
            'cufe_cude': cufe_cude['CUFE/CUDE'],
            'software_security_code_uncoded':
                software_security_code['SoftwareSecurityCodeUncoded'],
            'software_security_code':
                software_security_code['SoftwareSecurityCode']})
        _logger.info('lo q envia')
        _logger.info(self.invoice_id.payment_mean_code_id)
        return {
            'InvoiceAuthorization': active_dian_resolution['resolution_number'],
            'StartDate': active_dian_resolution['date_from'],
            'EndDate': active_dian_resolution['date_to'],
            'Prefix': active_dian_resolution['prefix'],
            'From': active_dian_resolution['number_from'],
            'To': active_dian_resolution['number_to'],
            'ProviderIDschemeID': supplier.check_digit,
            'ProviderIDschemeName': supplier.document_type_id.code,
            'ProviderID': NitOFE,
            'NitAdquiriente': NitAdq,
            'SoftwareID': IdSoftware,
            'SoftwareSecurityCode': software_security_code['SoftwareSecurityCode'],
            'QRCodeURL': QRCodeURL,
            'ProfileExecutionID': TipoAmbie,
            'ID': ID,
            'UUID': cufe_cude['CUFE/CUDE'],
            'IssueDate': IssueDate,
            'IssueTime': IssueTime,
            'LineCountNumeric': len(self.invoice_id.invoice_line_ids.filtered(lambda x: x.display_type not in ('line_section', 'line_note'))),
            'DocumentCurrencyCode': self.invoice_id.currency_id.name,
            'Delivery': customer._get_delivery_values(),
            'DeliveryTerms': {'LossRiskResponsibilityCode': LossRiskResponsibilityCode, 'LossRisk': LossRisk},
            'AccountingSupplierParty': supplier._get_accounting_partner_party_values(self.company_id),
            'AccountingCustomerParty': customer._get_accounting_partner_party_values(self.company_id),
            # TODO: No esta completamente calro los datos de que tercero son
            'TaxRepresentativeParty': supplier._get_tax_representative_party_values(),
            'InformationContentProviderParty': self.invoice_id.mandante_id._get_tax_representative_party_values() if self.invoice_id.mandante_id else {},
            'PaymentMeansID': self.invoice_id.payment_mean_id.code,
            'PaymentMeansCode': self.invoice_id.payment_mean_code_id.code or '10',
            #'PaymentMeansCode': self.invoice_id.payment_mean_code_id,
            #'PaymentDueDate': self.invoice_id.date_due,
            'DueDate': self.invoice_id.invoice_date_due,
            'PaymentExchangeRate': self.invoice_id._get_payment_exchange_rate(),
            'PaymentDueDate': self.invoice_id.invoice_date_due,
            'TaxesTotal': einvoicing_taxes['TaxesTotal'],
            'WithholdingTaxesTotal': einvoicing_taxes['WithholdingTaxesTotal'],
            'LineExtensionAmount': '{:.2f}'.format(self.invoice_id.amount_untaxed),
            'TaxExclusiveAmount': '{:.2f}'.format(self.invoice_id.amount_untaxed),
            'TaxInclusiveAmount': '{:.2f}'.format(TaxInclusiveAmount),#ValTot
            'PayableAmount': '{:.2f}'.format(PayableAmount),
            }

    def _get_invoice_values(self):
        xml_values = self._get_xml_values(False)
        #Punto 14.1.5.1. del anexo tecnico version 1.8
        #10 Estandar *
        #09 AIU
        #11 Mandatos
        #xml_values['CustomizationID'] = '10'
        xml_values['CustomizationID'] = self.invoice_id.operation_type
        active_dian_resolution = self.invoice_id._get_active_dian_resolution()

        xml_values['InvoiceControl'] = active_dian_resolution
        #Tipos de factura
        #Punto 14.1.3 del anexo tecnico version 1.8
        #01 Factura de Venta
        #02 Factura de Exportación
        #03 Factura por Contingencia Facturador
        #04 Factura por Contingencia DIAN
        xml_values['InvoiceTypeCode'] = self.invoice_id.invoice_type_code
        xml_values['InvoiceLines'] = self.invoice_id._get_invoice_lines()

        return xml_values

    def _get_attachment_values(self):
        xml_values = self._get_xml_values(False)
        #Punto 14.1.5.1. del anexo tecnico version 1.8
        #10 Estandar *
        #09 AIU
        #11 Mandatos
        #xml_values['CustomizationID'] = '10'
        xml_values['CustomizationID'] = self.invoice_id.operation_type
        active_dian_resolution = self.invoice_id._get_active_dian_resolution()

        xml_values['InvoiceControl'] = active_dian_resolution
        #Tipos de factura
        #Punto 14.1.3 del anexo tecnico version 1.8
        #01 Factura de Venta
        #02 Factura de Exportación
        #03 Factura por Contingencia Facturador
        #04 Factura por Contingencia DIAN
        xml_values['InvoiceTypeCode'] = self.invoice_id.invoice_type_code
        xml_values['InvoiceLines'] = self.invoice_id._get_invoice_lines()
        xml_values['ApplicationResponse'] = b64decode(self.ar_xml_file).decode("utf-8", "ignore")
        xml_values['xml_file'] = b64decode(self.xml_file).decode("utf-8", "ignore")

        return xml_values

    def _get_credit_note_values(self):
        xml_values = self._get_xml_values(False)
        if self.invoice_id.operation_type == '10' or self.invoice_id.reversed_entry_id:
            billing_reference = self.invoice_id._get_billing_reference()
        else:
            billing_reference = False

        #Punto 14.1.5.2. del anexo tecnico version 1.8
        #20 Nota Crédito que referencia una factura electrónica.
        #22 Nota Crédito sin referencia a facturas*.
        #23 Nota Crédito para facturación electrónica V1 (Decreto 2242).
        if billing_reference:
            xml_values['CustomizationID'] = '20'
            self.invoice_id.operation_type = '20'
        elif self.invoice_id.operation_type == '22':
            xml_values['CustomizationID'] = '22'
            self.invoice_id.operation_type = '22'
            billing_reference = {
                'ID': False,
                'UUID': False,
                'IssueDate': False,
                'CustomizationID': False}
        else:
            xml_values['CustomizationID'] = '20'
            self.invoice_id.operation_type = '20'
            billing_reference = {
                'ID': self.invoice_id.id_invoice_refound,
                'UUID': self.invoice_id.uuid_invoice,
                'IssueDate': self.invoice_id.issue_date_invoice or '',
                'CustomizationID': self.invoice_id.customizationid_invoice}

        #TODO 2.0: Exclusivo en referencias a documentos (elementos DocumentReference)
        #Punto 14.1.3 del anexo tecnico version 1.8
        #91 Nota Crédito
        xml_values['CreditNoteTypeCode'] = '91'
        xml_values['BillingReference'] = billing_reference
        xml_values['DiscrepancyReferenceID'] = billing_reference['ID']
        xml_values['DiscrepancyResponseCode'] = self.invoice_id.discrepancy_response_code_id.code
        xml_values['DiscrepancyDescription'] = self.invoice_id.discrepancy_response_code_id.name
        xml_values['CreditNoteLines'] = self.invoice_id._get_invoice_lines()
        return xml_values


    def _get_debit_note_values(self):
        xml_values = self._get_xml_values(False)
        if self.invoice_id.operation_type == '10' or self.invoice_id.debit_origin_id:
            billing_reference = self.invoice_id._get_billing_reference()
        else:
            billing_reference = False

        #Punto 14.1.5.3. del anexo tecnico version 1.8
        #30 Nota Débito que referencia una factura electrónica.
        #32 Nota Débito sin referencia a facturas *.
        #33 Nota Débito para facturación electrónica V1 (Decreto 2242).

        if billing_reference:
            xml_values['CustomizationID'] = '30'
            self.invoice_id.operation_type = '30'
        elif self.invoice_id.operation_type == '32':
            xml_values['CustomizationID'] = '32'
            self.invoice_id.operation_type = '32'
            billing_reference = {
                'ID': False,
                'UUID': False,
                'IssueDate': False,
                'CustomizationID': False}
        else:
            xml_values['CustomizationID'] = '30'
            self.invoice_id.operation_type = '30'
            billing_reference = {
                'ID': self.invoice_id.id_invoice_refound,
                'UUID': self.invoice_id.uuid_invoice,
                'IssueDate': self.invoice_id.issue_date_invoice,
                'CustomizationID': self.invoice_id.customizationid_invoice}
        #Exclusivo en referencias a documentos (elementos DocumentReference)
        #Punto 14.1.3 del anexo tecnico version 1.8
        #92 Nota Débito
        #TODO 2.0: DebitNoteTypeCode no existe en DebitNote
        #xml_values['DebitNoteTypeCode'] = '92'
        xml_values['BillingReference'] = billing_reference
        xml_values['DiscrepancyReferenceID'] = billing_reference['ID']
        xml_values['DiscrepancyResponseCode'] = self.invoice_id.discrepancy_response_code_id.code
        xml_values['DiscrepancyDescription'] = self.invoice_id.discrepancy_response_code_id.name
        xml_values['DebitNoteLines'] = self.invoice_id._get_invoice_lines()

        return xml_values

    def _get_xml_file(self):
        # if self.invoice_id.type == "out_invoice":
        #     xml_without_signature = global_functions.get_template_xml(
        #         self._get_invoice_values(),
        #         'Invoice')
        # elif self.invoice_id.type == "out_refund":
        #     xml_without_signature = global_functions.get_template_xml(
        #         self._get_credit_note_values(),
        #         'CreditNote')
        # elif self.invoice_id.type == "in_refund":
        #     xml_without_signature = global_functions.get_template_xml(
        #         self._get_debit_note_values(),
        #         'DebitNote')

        _logger.info('credit')
        _logger.info(self.invoice_id.refund_type)

        if self.invoice_id.move_type == "out_invoice" and not self.invoice_id.refund_type:
            xml_without_signature = global_functions.get_template_xml(
                self._get_invoice_values(),
                'Invoice')
        elif self.invoice_id.move_type == "out_refund" and self.invoice_id.refund_type != "debit":
            xml_without_signature = global_functions.get_template_xml(
                self._get_credit_note_values(),
                'CreditNote')
        elif self.invoice_id.move_type == "out_invoice" and self.invoice_id.refund_type == "debit":
            xml_without_signature = global_functions.get_template_xml(
                self._get_debit_note_values(),
                'DebitNote')

        xml_with_signature = global_functions.get_xml_with_signature(
            xml_without_signature,
            self.company_id.signature_policy_url,
            self.company_id.signature_policy_description,
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        return xml_with_signature

    def _get_zipped_file(self):
        output = BytesIO()
        zipfile = ZipFile(output, mode='w')
        zipfile_content = BytesIO()
        zipfile_content.write(b64decode(self.xml_file))
        zipfile.writestr(self.xml_filename, zipfile_content.getvalue())
        zipfile.close()
        return output.getvalue()

    def action_set_files(self):
        if not self.xml_filename or not self.zipped_filename:
            self._set_filenames()

        self.write({'xml_file': b64encode(self._get_xml_file()).decode("utf-8", "ignore")})
        self.write({'zipped_file': b64encode(self._get_zipped_file()).decode("utf-8", "ignore")})


    def _get_SendTestSetAsync_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)


        #_logger.info('ZIPPER2')

        xml_soap_values['fileName'] = self.zipped_filename.replace('.zip', '')
        xml_soap_values['contentFile'] = self.zipped_file.decode("utf-8", "ignore")
        xml_soap_values['testSetId'] = self.company_id.test_set_id

        return xml_soap_values

    def _get_SendBillAsync_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['fileName'] = self.zipped_filename.replace('.zip', '')
        xml_soap_values['contentFile'] = self.zipped_file.decode("utf-8", "ignore")

        return xml_soap_values




    def action_sent_zipped_file(self):
        # if self._get_GetStatus(False):
        #     return True

        msg1 = _("Unknown Error,\nStatus Code: %s,\nReason: %s,\n\nContact with your administrator "
                "or you can choose a journal with a Contingency Checkbook E-Invoicing sequence "
                "and change the Invoice Type to 'Factura por Contingencia Facturador'.")
        msg2 = _("Unknown Error: %s\n\nContact with your administrator "
                "or you can choose a journal with a Contingency Checkbook E-Invoicing sequence "
                "and change the Invoice Type to 'Factura por Contingencia Facturador'.")
        b = "http://schemas.datacontract.org/2004/07/UploadDocumentResponse"
        wsdl = DIAN['wsdl-hab']

        _logger.info('entrooo action sent_zipped')

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']
            _logger.info('entrooo produccion')
            SendBillAsync_values = self._get_SendBillAsync_values()
            SendBillAsync_values['To'] = wsdl.replace('?wsdl', '')
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(SendBillAsync_values, 'SendBillSync'),
                SendBillAsync_values['Id'],
                self.company_id.certificate_file,
                self.company_id.certificate_password)
        else:
            SendTestSetAsync_values = self._get_SendTestSetAsync_values()
            SendTestSetAsync_values['To'] = wsdl.replace('?wsdl', '')
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(SendTestSetAsync_values, 'SendTestSetAsync'),
                SendTestSetAsync_values['Id'],
                self.company_id.certificate_file,
                self.company_id.certificate_password)

        try:
            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature, encoding="unicode"))
            _logger.info('respuesta post')
            _logger.info(response.status_code)
            if response.status_code == 200:
                if self.company_id.profile_execution_id == '1':
                    self.write({'state': 'sent'})
                    self._get_status_response(response,send_mail=False)
                else:
                    root = etree.fromstring(response.text)

                    for element in root.iter("{%s}ZipKey" % b):
                        self.write({'zip_key': element.text, 'state': 'sent'})
                        self.action_GetStatusZip()
            elif response.status_code in (500, 503, 507):
                dian_document_line_obj = self.env['account.invoice.dian.document.line']
                dian_document_line_obj.create({
                    'dian_document_id': self.id,
                    'send_async_status_code': response.status_code,
                    'send_async_reason': response.reason,
                    'send_async_response': response.text})
            else:
                raise ValidationError(msg1 % (response.status_code, response.reason))
        except exceptions.RequestException as e:
            raise ValidationError(msg2 % (e))

        return True



    def sent_zipped_file(self):
        b = "http://schemas.datacontract.org/2004/07/UploadDocumentResponse"

        if self.company_id.profile_execution_id == '1':
            _logger.info('entro if')
            SendBillAsync_values = self._get_SendBillAsync_values()
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(
                    SendBillAsync_values,
                    'SendBillAsync'),
                SendBillAsync_values['Id'],
                self.company_id.certificate_file,
                self.company_id.certificate_password)
        elif self.company_id.profile_execution_id == '2':
            _logger.info('entro else')
            SendTestSetAsync_values = self._get_SendTestSetAsync_values()
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(
                    SendTestSetAsync_values,
                    'SendTestSetAsync'),
                SendTestSetAsync_values['Id'],
                self.company_id.certificate_file,
                self.company_id.certificate_password)

        response = post(
            DIAN['wsdl-hab'],
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature, encoding = "unicode"))

        _logger.info(etree.tostring(xml_soap_with_signature, encoding = "unicode"))
        _logger.info('response 1')
        _logger.info(response)

        if response.status_code == 200:
            root = etree.fromstring(response.text)

            for element in root.iter("{%s}ZipKey" % b):
                self.write({'zip_key': element.text, 'state': 'sent'})
        else:
            raise ValidationError(response.status_code)

    def _get_GetStatusZip_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        xml_soap_values['trackId'] = self.zip_key

        return xml_soap_values


    def _get_GetStatus(self, send_mail):
        msg1 = _("Unknown Error,\nStatus Code: %s,\nReason: %s"
                 "\n\nContact with your administrator.")
        msg2 = _("Unknown Error: %s\n\nContact with your administrator.")
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']

        GetStatus_values = self._get_GetStatus_values()
        GetStatus_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetStatus_values, 'GetStatus'),
            GetStatus_values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        try:
            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature, encoding = "unicode"))

            if response.status_code == 200:
                _logger.info('_get_GetStatus')
                return self._get_status_response(response, send_mail)
            else:
                raise ValidationError(msg1 % (response.status_code, response.reason))
        except exceptions.RequestException as e:
            raise ValidationError(msg2 % (e))

    def action_GetStatusZip(self):
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_id == '1':
            wsdl = DIAN['wsdl']

        GetStatusZip_values = self._get_GetStatusZip_values()
        GetStatusZip_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetStatusZip_values, 'GetStatusZip'),
            GetStatusZip_values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        response = post(
            wsdl,
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature, encoding = "unicode"))

        if response.status_code == 200:
            self._get_status_response(response,send_mail=False)
        else:
            raise ValidationError(response.status_code)

        return True

    def GetStatusZip(self):
        b = "http://schemas.datacontract.org/2004/07/DianResponse"
        c = "http://schemas.microsoft.com/2003/10/Serialization/Arrays"
        s = "http://www.w3.org/2003/05/soap-envelope"
        strings = ''
        status_code = 'other'
        GetStatusZip_values = self._get_GetStatusZip_values()
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(
                GetStatusZip_values,
                'GetStatusZip'),
            GetStatusZip_values['Id'],
            self.company_id.certificate_file,
            self.company_id.certificate_password)

        response = post(
            DIAN['wsdl-hab'],
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature, encoding = "unicode"))

        _logger.info('response 2')
        _logger.info(response)
        if response.status_code == 200:
            #root = etree.fromstring(response.content)
            #root = etree.tostring(root, encoding='utf-8')
            root = etree.fromstring(response.content)

            for element in root.iter("{%s}StatusCode" % b):
                if element.text in ('00', '66', '90', '99'):
                    if element.text == '00':
                        self.write({'state': 'done'})

                        if self.invoice_id.move_type == 'out_invoice':
                            self.company_id.out_invoice_sent += 1
                        elif self.invoice_id.move_type == 'out_refund':
                            self.company_id.out_refund_sent += 1
                        elif self.invoice_id.move_type == 'in_refund':
                            self.company_id.in_refund_sent += 1

                    status_code = element.text
            if status_code == '00':
                for element in root.iter("{%s}StatusMessage" % b):
                    strings = element.text

            for element in root.iter("{%s}string" % c):
                if strings == '':
                    strings = '- ' + element.text
                else:
                    strings += '\n\n- ' + element.text

            if strings == '':
                for element in root.iter("{%s}Body" % s):
                    strings = etree.tostring(element, pretty_print=True)

                if strings == '':
                    strings = etree.tostring(root, pretty_print=True)

            self.write({
                'get_status_zip_status_code': status_code,
                'get_status_zip_response': strings})
        else:
            raise ValidationError(response.status_code)

    def action_reprocess(self):
        self.write({'xml_file': b64encode(self._get_xml_file()).decode("utf-8", "ignore")})
        self.write({'zipped_file': b64encode(self._get_zipped_file()).decode("utf-8", "ignore")})
        self.sent_zipped_file()
        self.GetStatusZip()

    def change_cufe(self):
        if 'procesado anteriormente.' in self.get_status_zip_response and not self.origin_cufe_cude:
            cufe_origin = self.cufe_cude
            new_cufe = self.get_status_zip_response.replace("- Regla: 90, Rechazo: Documento con CUFE '", '').replace("' procesado anteriormente.", '')
            self.origin_cufe_cude = cufe_origin
            self.cufe_cude = new_cufe
        else:
            raise ValidationError('El cufe no ha sido procesado anteriormente')
    
    def return_cufe(self):
        if self.origin_cufe_cude:
            self.cufe_cude = self.origin_cufe_cude
            self.origin_cufe_cude = ''
            

class AccountInvoiceDianDocumentLine(models.Model):
    _name = "account.invoice.dian.document.line"

    dian_document_id = fields.Many2one(
        comodel_name='account.invoice.dian.document',
        string='DIAN Document')
    send_async_status_code = fields.Char(string='Status Code')
    send_async_reason = fields.Char(string='Reason')
    send_async_response = fields.Text(string='Response')