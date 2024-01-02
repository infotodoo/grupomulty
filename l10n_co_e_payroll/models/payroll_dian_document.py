# -*- coding: utf-8 -*-
# Copyright 2021 Diego Carvajal <Github@diegoivanc>

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

class PayrollDianDocument(models.Model):
    _name = "payroll.dian.document"
    _inherit = ['mail.thread']
    _rec_name = 'nomina_id'

    state = fields.Selection([('draft', 'Draft'),
                              ('sent', 'Sent'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel')], string='State', readonly=True, default='draft', tracking=True)
    nomina_id = fields.Many2one('payroll.dian', string='Nomina')
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
    dian_document_line_ids = fields.One2many('payroll.dian.document.line', 'dian_document_id', string='DIAN Document Lines')
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
        for record in self:



            date_format = str(record.nomina_id.create_date)[0:19]
            create_date = datetime.strptime(date_format, '%Y-%m-%d %H:%M:%S')
            create_date = create_date.replace(tzinfo=timezone('UTC'))
            nit_fac = record.company_id.nit_e_payroll
            nit_adq = record.nomina_id.numero_documento
            cufe = record.cufe_cude
            number = record.nomina_id.name
            ValDev = self.nomina_id.total_devengados
            ValDed = self.nomina_id.total_deducciones
            ValTolNE = ValDev - ValDed
            IssueDate = self.nomina_id.fecha_liquidacion
            IssueTime = create_date.astimezone(
                timezone('America/Bogota')).strftime('%H:%M:%S-05:00')


            qr_data = "NumNIE: " + number if number else 'NO_VALIDADA'
            qr_data += "\nFecNIE: " + str(IssueDate) if str(IssueDate) else ''
            qr_data += "\nHorNIE: " + str(IssueTime) if str(IssueTime) else ''
            qr_data += "\nNitNIE: " + str(nit_fac) if str(nit_fac) else ''
            qr_data += "\nDocEmp: " + nit_adq if nit_adq else ''
            qr_data += "\nValDev: " + '{:.2f}'.format(ValDev)
            qr_data += "\nValDed: " + '{:.2f}'.format(ValDed)
            qr_data += "\nValTol: " + '{:.2f}'.format(ValTolNE)
            qr_data += "\nCUNE: " + cufe if cufe else ''
            qr_data += "\n\n" + record.invoice_url if record.invoice_url else ''

            record.qr_image = global_functions.get_qr_code(qr_data)

    def _generate_qr_codecopia(self):
        einvoicing_taxes = self.invoice_id._get_einvoicing_taxes()
        ValImp1 = einvoicing_taxes['TaxesTotal']['01']['total']
        ValImp2 = einvoicing_taxes['TaxesTotal']['04']['total']
        ValImp3 = einvoicing_taxes['TaxesTotal']['03']['total']
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
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)

        xml_soap_values['trackId'] = self.cufe_cude
        _logger.info('trackid')
        _logger.info(self.cufe_cude)

        return xml_soap_values



    def action_GetStatus(self):
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_payroll_id == '1':
            wsdl = DIAN['wsdl']

        GetStatus_values = self._get_GetStatus_values()
        GetStatus_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetStatus_values, 'GetStatus'),
            GetStatus_values['Id'],
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)

        response = post(
            wsdl,
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature, encoding="unicode"))

        if response.status_code == 200:
            self._get_status_response(response,send_mail=False)
        else:
            raise ValidationError(response.status_code)

        return True

    def action_GetStatusMulti(self):
        wsdl = DIAN['wsdl-hab']

        for record in self:
            if record.company_id.profile_execution_payroll_id == '1':
                wsdl = DIAN['wsdl']

            GetStatus_values = record._get_GetStatus_values()
            GetStatus_values['To'] = wsdl.replace('?wsdl', '')
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(GetStatus_values, 'GetStatus'),
                GetStatus_values['Id'],
                record.company_id.payroll_certificate_file,
                record.company_id.payroll_certificate_password)

            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature, encoding="unicode"))

            if response.status_code == 200:
                record._get_status_response(response, send_mail=False)
            else:
                raise ValidationError(response.status_code)

        return True


    def _get_pdf_file(self):
        template = self.env['ir.actions.report'].browse(self.company_id.report_template.id)
        #pdf = self.env.ref('account.move').render_qweb_pdf([self.invoice_id.id])[0]
        if template:
            pdf = template.render_qweb_pdf(self.invoice_id.id)
        else:
            pdf = self.env.ref('account.account_invoices').render_qweb_pdf(self.invoice_id.id)
        pdf = base64.b64encode(pdf[0])
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
        if xml_attachment_file:
            attach_ids.append(xml_attachment_file.id)

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


        for element in root.iter("{%s}StatusCode" % b):
            _logger.info('entro element')
            _logger.info(element.text)

            if element.text in ('0', '00', '66', '90', '99'):
                if element.text == '00':
                    self.write({'state': 'done'})
                    self.company_id.out_nomina_sent += 1

                status_code = element.text
        if status_code == '0':
            self.action_GetStatus()

            return True

        if status_code == '00':
            _logger.info('estatus code 00')
            _logger.info(status_code)
            for element in root.iter("{%s}StatusMessage" % b):
                _logger.info('element statusmessage')
                _logger.info(element.text)
                strings = element.text

            for element in root.iter("{%s}XmlBase64Bytes" % b):
                _logger.info('element xmlbase')
                _logger.info(element.text)
                self.write({'ar_xml_file': element.text})

            #if not self.mail_sent:
                #self.action_send_mail()
            to_return = True
        else:
            #if send_mail:
            #    self.send_failure_email()
            #self.send_failure_email()
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
        subject = _('ALERTA! La Factura %s no fue enviada a la DIAN.') % self.nomina_id.name
        msg_body = _('''Cordial Saludo,<br/><br/>La factura ''' + self.nomina_id.name +
                     ''' del cliente ''' + self.nomina_id.partner_id.name + ''' no pudo ser ''' +
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
        nit = str(self.company_id.nit_e_payroll)
        if self.company_id.nit_e_payroll:
            nnnnnnnnnn = nit.zfill(10)
        else:
            raise ValidationError("The company identification document is not "
                                  "established in the partner.\n\nGo to Contacts > "
                                  "[Your company name] to configure it.")
        #El Código “ppp” es 000 para Software Propio
        ppp = '21'
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
        out_invoice_sent = 1
        out_refund_sent = 1
        in_refund_sent = 1
        zip_sent = out_invoice_sent + out_refund_sent + in_refund_sent

        xml_filename_prefix = 'nie'
        dddddddd = str(self.company_id.out_nomina_sent + 1).zfill(8)

        zdddddddd = str(self.company_id.out_nomina_sent + 1).zfill(8)
        nnnnnnnnnnpppaadddddddd = nnnnnnnnnn + aa + dddddddd
        znnnnnnnnnnpppaadddddddd = nnnnnnnnnn + aa + zdddddddd

        self.write({
            'xml_filename': xml_filename_prefix + nnnnnnnnnnpppaadddddddd + '.xml',
            'zipped_filename': 'z' + znnnnnnnnnnpppaadddddddd + '.zip'})



    def _get_xml_values(self, ClTec):
        msg7 = _('The Incoterm is not defined for this export type invoice')

        #active_dian_resolution = self.invoice_id._get_active_dian_resolution()
        #einvoicing_taxes = self.invoice_id._get_einvoicing_taxes()
        date_format = str(self.create_date)[0:19]
        _logger.info(date_format)
        create_date = datetime.strptime(date_format, '%Y-%m-%d %H:%M:%S')
        create_date = create_date.replace(tzinfo=timezone('UTC'))
        ID = self.nomina_id.name
        IssueDate = self.nomina_id.fecha_liquidacion
        IssueTime = create_date.astimezone(
            timezone('America/Bogota')).strftime('%H:%M:%S-05:00')

        LossRiskResponsibilityCode = self.invoice_id.invoice_incoterm_id.code or ''
        LossRisk = self.invoice_id.invoice_incoterm_id.name or ''
        # if self.invoice_id.invoice_type_code == '02':
        #     if not self.invoice_id.invoice_incoterm_id:
        #         raise UserError(msg7)
        #     elif not self.invoice_id.invoice_incoterm_id.name or not self.invoice_id.invoice_incoterm_id.code:
        #         raise UserError('Incoterm is not properly parameterized')
        #     else:
        #         LossRiskResponsibilityCode = self.invoice_id.invoice_incoterm_id.code
        #         LossRisk = self.invoice_id.invoice_incoterm_id.name

        supplier = self.company_id.partner_id
        customer = self.invoice_id.partner_id
        NitOFE = self.company_id.nit_e_payroll
        Nitdv = self.company_id.dv_e_payroll
        empresa_departamento = self.company_id.departamento
        empresa_municipio = self.company_id.municipio
        empresa_direccion = self.company_id.street
        NameCompany = supplier.name
        NitAdq = self.nomina_id.numero_documento

        ClTec = False
        SoftwarePIN = False
        IdSoftware = self.company_id.payroll_software_id

        #ClTec = active_dian_resolution['technical_key']

        SoftwarePIN = self.company_id.payroll_software_pin

        TipoAmbie = self.company_id.profile_execution_payroll_id

        if TipoAmbie == '1':
            QRCodeURL = DIAN['catalogo']
        else:
            QRCodeURL = DIAN['catalogo-hab']

        ValFac = self.invoice_id.amount_untaxed
        ValDev = self.nomina_id.total_devengados
        ValDed = self.nomina_id.total_deducciones
        ValTolNE = ValDev - ValDed
        TipoXML = self.nomina_id.tipo_nomina
        TipoNota = self.nomina_id.nota_ajuste

        if TipoXML == '102' or TipoNota == '1' :
            cufe_cude = global_functions.get_cune(
                ID,
                IssueDate,
                IssueTime,
                str('{:.2f}'.format(ValDev)),
                str('{:.2f}'.format(ValDed)),
                str('{:.2f}'.format(ValTolNE)),
                NitOFE,
                NitAdq,
                TipoXML,
                SoftwarePIN,
                TipoAmbie)
        else:
            cufe_cude = global_functions.get_cune(
                ID,
                IssueDate,
                IssueTime,
                str('{:.2f}'.format(0.00)),
                str('{:.2f}'.format(0.00)),
                str('{:.2f}'.format(0.00)),
                NitOFE,
                0,
                TipoXML,
                SoftwarePIN,
                TipoAmbie)
        software_security_code = global_functions.get_software_security_code(
            IdSoftware,
            self.company_id.payroll_software_pin,
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
        return {
            'CompanyID': NameCompany,
            'ProviderID': NitOFE,
            'NitAdquiriente': NitAdq,
            'Nitdv': Nitdv,
            'empresa_departamento': empresa_departamento,
            'empresa_municipio': empresa_municipio,
            'empresa_direccion': empresa_direccion,
            'SoftwareID': IdSoftware,
            'SoftwareSecurityCode': software_security_code['SoftwareSecurityCode'],
            'QRCodeURL': QRCodeURL,
            'ProfileExecutionID': TipoAmbie,
            'ID': ID,
            'CUNE': cufe_cude['CUFE/CUDE'],
            'IssueDate': IssueDate,
            'IssueTime': IssueTime,
            'DeliveryTerms': {'LossRiskResponsibilityCode': LossRiskResponsibilityCode, 'LossRisk': LossRisk},
            # TODO: No esta completamente calro los datos de que tercero son
            #'PaymentMeansCode': self.invoice_id.payment_mean_code_id,
            #'PaymentDueDate': self.invoice_id.date_due,
            'DueDate': self.invoice_id.invoice_date_due,
            'PaymentDueDate': self.invoice_id.invoice_date_due,
            'ValDev': '{:.2f}'.format(ValDev),
            'ValDed': '{:.2f}'.format(ValDed),
            'ValTolNE': '{:.2f}'.format(ValTolNE),
            'NominaGeneral': self.nomina_id,
            }

    def _get_invoice_values(self):
        xml_values = self._get_xml_values(False)
        #Punto 14.1.5.1. del anexo tecnico version 1.8
        #10 Estandar *
        #09 AIU
        #11 Mandatos
        #xml_values['CustomizationID'] = '10'
        #xml_values['CustomizationID'] = self.invoice_id.operation_type
        #active_dian_resolution = self.invoice_id._get_active_dian_resolution()

        #xml_values['InvoiceControl'] = active_dian_resolution
        #Tipos de factura
        #Punto 14.1.3 del anexo tecnico version 1.8
        #01 Factura de Venta
        #02 Factura de Exportación
        #03 Factura por Contingencia Facturador
        #04 Factura por Contingencia DIAN
        _logger.info('invoiceline')
        _logger.info('invoiceline')
        _logger.info('invoiceline')
        _logger.info('invoiceline')

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

        if self.nomina_id.tipo_nomina == '102':
            _logger.info('nomina')
            xml_without_signature = global_functions.get_template_xml(
                self._get_invoice_values(),
                'Nomina')
        else:
            _logger.info('ajuste')
            xml_without_signature = global_functions.get_template_xml(
                self._get_invoice_values(),
                'NominaAjuste')

        xml_with_signature = global_functions.get_xml_with_signature(
            xml_without_signature,
            self.company_id.payroll_signature_policy_url,
            self.company_id.payroll_signature_policy_description,
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)

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
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)


        _logger.info('ZIPPER2')

        xml_soap_values['fileName'] = self.zipped_filename.replace('.zip', '')
        xml_soap_values['contentFile'] = self.zipped_file.decode("utf-8", "ignore")
        xml_soap_values['testSetId'] = self.company_id.payroll_test_set_id

        return xml_soap_values

    def _get_SendBillAsync_values(self):
        xml_soap_values = global_functions.get_xml_soap_values(
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)

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

        if self.company_id.profile_execution_payroll_id == '1':
            wsdl = DIAN['wsdl']
            _logger.info('entrooo produccion')
            SendBillAsync_values = self._get_SendBillAsync_values()
            SendBillAsync_values['To'] = wsdl.replace('?wsdl', '')
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(SendBillAsync_values, 'SendNominaSync'),
                SendBillAsync_values['Id'],
                self.company_id.payroll_certificate_file,
                self.company_id.payroll_certificate_password)
        else:
            SendTestSetAsync_values = self._get_SendTestSetAsync_values()
            SendTestSetAsync_values['To'] = wsdl.replace('?wsdl', '')
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(SendTestSetAsync_values, 'SendTestSetAsync'),
                SendTestSetAsync_values['Id'],
                self.company_id.payroll_certificate_file,
                self.company_id.payroll_certificate_password)

        try:
            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature, encoding="unicode"))
            _logger.info('respuesta post')
            _logger.info(response.status_code)
            if response.status_code == 200:
                if self.company_id.profile_execution_payroll_id == '1':
                    self.write({'state': 'sent'})
                    self._get_status_response(response,send_mail=False)
                else:
                    root = etree.fromstring(response.text)
                    _logger.info('response.text')
                    _logger.info(response.text)

                    for element in root.iter("{%s}ZipKey" % b):
                        self.write({'zip_key': element.text, 'state': 'sent'})
                        self.action_GetStatusZip()
            elif response.status_code in (500, 503, 507):
                dian_document_line_obj = self.env['payroll.dian.document.line']
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

        if self.company_id.profile_execution_payroll_id == '1':
            _logger.info('entro if')
            SendBillAsync_values = self._get_SendBillAsync_values()
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(
                    SendBillAsync_values,
                    'SendBillAsync'),
                SendBillAsync_values['Id'],
                self.company_id.payroll_certificate_file,
                self.company_id.payroll_certificate_password)
        elif self.company_id.profile_execution_payroll_id == '2':
            _logger.info('entro else')
            SendTestSetAsync_values = self._get_SendTestSetAsync_values()
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(
                    SendTestSetAsync_values,
                    'SendTestSetAsync'),
                SendTestSetAsync_values['Id'],
                self.company_id.payroll_certificate_file,
                self.company_id.payroll_certificate_password)

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
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)

        xml_soap_values['trackId'] = self.zip_key

        return xml_soap_values


    def _get_GetStatus(self, send_mail):
        msg1 = _("Unknown Error,\nStatus Code: %s,\nReason: %s"
                 "\n\nContact with your administrator.")
        msg2 = _("Unknown Error: %s\n\nContact with your administrator.")
        wsdl = DIAN['wsdl-hab']

        if self.company_id.profile_execution_payroll_id == '1':
            wsdl = DIAN['wsdl']

        GetStatus_values = self._get_GetStatus_values()
        GetStatus_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetStatus_values, 'GetStatus'),
            GetStatus_values['Id'],
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)

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

        if self.company_id.profile_execution_payroll_id == '1':
            wsdl = DIAN['wsdl']

        GetStatusZip_values = self._get_GetStatusZip_values()
        GetStatusZip_values['To'] = wsdl.replace('?wsdl', '')
        xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
            global_functions.get_template_xml(GetStatusZip_values, 'GetStatusZip'),
            GetStatusZip_values['Id'],
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)

        response = post(
            wsdl,
            headers={'content-type': 'application/soap+xml;charset=utf-8'},
            data=etree.tostring(xml_soap_with_signature, encoding = "unicode"))
        _logger.info('response.text')
        _logger.info(response.status_code)
        _logger.info(response.text)

        if response.status_code == 200:
            _logger.info('entro if')
            self._get_status_response(response,send_mail=False)
        else:
            _logger.info('entro else')
            raise ValidationError(response.status_code)

        return True

    def action_GetStatusZipmulti(self):
        wsdl = DIAN['wsdl-hab']


        for record in self:
            if record.company_id.profile_execution_payroll_id == '1':
                wsdl = DIAN['wsdl']

            GetStatusZip_values = record._get_GetStatusZip_values()
            GetStatusZip_values['To'] = wsdl.replace('?wsdl', '')
            xml_soap_with_signature = global_functions.get_xml_soap_with_signature(
                global_functions.get_template_xml(GetStatusZip_values, 'GetStatusZip'),
                GetStatusZip_values['Id'],
                record.company_id.payroll_certificate_file,
                record.company_id.payroll_certificate_password)

            response = post(
                wsdl,
                headers={'content-type': 'application/soap+xml;charset=utf-8'},
                data=etree.tostring(xml_soap_with_signature, encoding = "unicode"))
            _logger.info('response.text')
            _logger.info(response.status_code)
            _logger.info(response.text)

            if response.status_code == 200:
                _logger.info('entro if')
                record._get_status_response(response,send_mail=False)
            else:
                _logger.info('entro else')
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
            self.company_id.payroll_certificate_file,
            self.company_id.payroll_certificate_password)

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

                        if self.invoice_id.type == 'out_invoice':
                            self.company_id.out_invoice_sent += 1
                        elif self.invoice_id.type == 'out_refund':
                            self.company_id.out_refund_sent += 1
                        elif self.invoice_id.type == 'in_refund':
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
            

class PayrollDianDocumentLine(models.Model):
    _name = "payroll.dian.document.line"

    dian_document_id = fields.Many2one(
        comodel_name='payroll.dian.document',
        string='DIAN Document')
    send_async_status_code = fields.Char(string='Status Code')
    send_async_reason = fields.Char(string='Reason')
    send_async_response = fields.Text(string='Response')