# -*- coding: utf-8 -*-

import hashlib
from os import path
from uuid import uuid4
from base64 import b64encode, b64decode
#from StringIO import StringIO
from io import StringIO ## for Python 3
from io import BytesIO
from datetime import datetime, date, timedelta
from OpenSSL import crypto
import xmlsig
from lxml import etree
from xades import XAdESContext, template
from xades.policy import GenericPolicyId
from pytz import timezone
from jinja2 import Environment, FileSystemLoader
from odoo import _
from odoo.exceptions import ValidationError
#from mock import patch
from unidecode import unidecode
from qrcode import QRCode, constants

import logging
_logger = logging.getLogger(__name__)


def get_cuds(
        NumFac,
        FecFac,
        HorFac,
        ValFac,
        CodImp1,
        ValImp1,
        ValTot,
        NitOFE,
        NumAdq,
        SoftwarePIN,
        TipoAmbie):
    uncoded_value = (NumFac + ' + ' + str(FecFac) + ' + ' + str(HorFac) + ' + ' +
                     ValFac + ' + ' + CodImp1 + ' + ' + ValImp1 + ' + ' +
                     ValTot + ' + ' + NitOFE + ' + ' + NumAdq + ' + ' +
                     SoftwarePIN + ' + ' + TipoAmbie)
    unicode = unidecode(
        str(NumFac) + str(FecFac) + str(HorFac) + str(ValFac) + str(CodImp1) + str(ValImp1) + str(ValTot) + str(
            NitOFE) + str(NumAdq) + str(SoftwarePIN) + str(TipoAmbie)).encode()

    CUFE_CUDE = hashlib.sha384(unicode)

    return {
        'CUFE/CUDEUncoded': uncoded_value,
        'CUFE/CUDE': CUFE_CUDE.hexdigest()}


def get_cufe_cude(
        NumFac,
        FecFac,
        HorFac,
        ValFac,
        CodImp1,
        ValImp1,
        CodImp2,
        ValImp2,
        CodImp3,
        ValImp3,
        ValTot,
        NitOFE,
        NumAdq,
        ClTec,
        SoftwarePIN,
        TipoAmbie):

    #CUFE = SHA-384(NumFac + FecFac + HorFac + ValFac + CodImp1 + ValImp1 +
    # CodImp2 + ValImp2 + CodImp3 + ValImp3 + ValTot + NitOFE + NumAdq +
    # ClTec + TipoAmbie)
    #CUDE = SHA-384(NumFac + FecFac + HorFac + ValFac + CodImp1 + ValImp1 +
    # CodImp2 + ValImp2 + CodImp3 + ValImp3 + ValTot + NitOFE + NumAdq +
    # Software-PIN + TipoAmbie)
    uncoded_value = (NumFac + ' + ' + str(FecFac) + ' + ' + str(HorFac) + ' + ' +
                     ValFac + ' + ' + CodImp1 + ' + ' + ValImp1 + ' + ' +
                     CodImp2 + ' + ' + ValImp2 + ' + ' + CodImp3 + ' + ' +
                     ValImp3 + ' + ' + ValTot + ' + ' + NitOFE + ' + ' +
                     NumAdq + ' + ' + (ClTec if ClTec else SoftwarePIN) +
                     ' + ' + TipoAmbie)
    unicode = unidecode(NumFac + str(FecFac) + str(HorFac) + ValFac + CodImp1 + ValImp1 + CodImp2 +
        ValImp2 + CodImp3 + ValImp3 + ValTot + NitOFE + NumAdq +
        (ClTec if ClTec else SoftwarePIN) + TipoAmbie).encode()

    CUFE_CUDE = hashlib.sha384(unicode)

    return {
        'CUFE/CUDEUncoded': uncoded_value,
        'CUFE/CUDE': CUFE_CUDE.hexdigest()}

def get_software_security_code(IdSoftware, Pin, NroDocumentos):
    uncoded_value = (IdSoftware + ' + ' + Pin + ' + ' + NroDocumentos)
    software_security_code = hashlib.sha384(unidecode(IdSoftware + Pin + NroDocumentos).encode())

    return {
        'SoftwareSecurityCodeUncoded': uncoded_value,
        'SoftwareSecurityCode': software_security_code.hexdigest()}

#https://stackoverflow.com/questions/38432809/dynamic-xml-template-generation-using-get-template-jinja2
def get_template_xml(values, template_name):
    base_path = path.dirname(path.dirname(__file__))
    env = Environment(loader=FileSystemLoader(path.join(
        base_path,
        'templates')))
    template_xml = env.get_template('{}.xml'.format(template_name))
    xml = template_xml.render(values)

    return xml.replace('&', '&amp;').replace('&amp;amp;', '&amp;')

   
#https://github.com/etobella/python-xades
def get_xml_with_signature(
        xml_without_signature,
        signature_policy_url,
        signature_policy_description,
        certificate_file,
        certificate_password):
    ##https://github.com/etobella/python-xades/blob/master/test/base.py
    #base_path = path.dirname(path.dirname(__file__))
    #root = etree.parse(path.join(base_path, name)).getroot()
    #https://lxml.de/tutorial.html
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_without_signature.encode("utf-8"),parser=parser)
    #https://github.com/etobella/python-xades/blob/master/test/test_xades.py
    signature_id = "xmldsig-{}".format(uuid4())
    signature = xmlsig.template.create(
        xmlsig.constants.TransformInclC14N,
        xmlsig.constants.TransformRsaSha512,
        signature_id)
    ref = xmlsig.template.add_reference(
        signature,
        xmlsig.constants.TransformSha512,
        uri="",
        name=signature_id + "-ref0")
    xmlsig.template.add_transform(
        ref,
        xmlsig.constants.TransformEnveloped)
    xmlsig.template.add_reference(
        signature,
        xmlsig.constants.TransformSha512,
        uri="#" + signature_id + "-keyinfo")
    xmlsig.template.add_reference(
        signature,
        xmlsig.constants.TransformSha512,
        uri="#" + signature_id + "-signedprops",
        uri_type="http://uri.etsi.org/01903#SignedProperties")
    ki = xmlsig.template.ensure_key_info(
        signature,
        name=signature_id + "-keyinfo")
    data = xmlsig.template.add_x509_data(ki)
    xmlsig.template.x509_data_add_certificate(data)
    serial = xmlsig.template.x509_data_add_issuer_serial(data)
    xmlsig.template.x509_issuer_serial_add_issuer_name(serial)
    xmlsig.template.x509_issuer_serial_add_serial_number(serial)
    xmlsig.template.add_key_value(ki)
    qualifying = template.create_qualifying_properties(signature)
    props = template.create_signed_properties(
        qualifying,
        name=signature_id + "-signedprops")
    template.add_claimed_role(props, "supplier")
    policy = GenericPolicyId(
        signature_policy_url,
        signature_policy_description,
        xmlsig.constants.TransformSha512)
    root.append(signature)
    ctx = XAdESContext(policy)
    ctx.load_pkcs12(get_pkcs12(certificate_file, certificate_password))
    #with patch("xades.policy.urllib.urlopen") as mock:
    #    mock.return_value = b64decode(signature_policy_file).read()
    ctx.sign(signature)
    #ctx.verify(signature)

    #Se debe firmar en un paso anterior, y luego remover el signature para
    #ubicarlo en posicion necesaria
    root.remove(signature)
    ext = "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
    ds = "http://www.w3.org/2000/09/xmldsig#"
    position = 0

    #https://lxml.de/tutorial.html
    for element in root.iter("{%s}ExtensionContent" % ext):
        if position == 1:
            element.append(signature)
        position += 1

    #Complememto para añadir atributo faltante
    for element in root.iter("{%s}SignatureValue" % ds):
        element.attrib['Id'] = signature_id + "-sigvalue"

    #https://www.decalage.info/en/python/lxml-c14n
    output = BytesIO()
    root.getroottree().write_c14n(output)#, exclusive=1, with_comments=0
    root = output.getvalue()
    #_logger.info(root)
    return root

def get_pkcs12(certificate_file, certificate_password):
    try:
        return crypto.load_pkcs12(
            b64decode(certificate_file),
            certificate_password)
    except Exception as e:
        raise ValidationError(_("The cretificate password or certificate file is not"
                                " valid.\nException: %s") % e)

def get_xml_soap_values(certificate_file, certificate_password):
    Created = datetime.now().replace(tzinfo=timezone('UTC'))
    Created = Created.astimezone(timezone('UTC'))
    Expires = (Created + timedelta(seconds=60000)).strftime('%Y-%m-%dT%H:%M:%S.001Z')
    Created = Created.strftime('%Y-%m-%dT%H:%M:%S.001Z')
    #https://github.com/mit-dig/idm/blob/master/idm_query_functions.py#L151
    pkcs12 = get_pkcs12(certificate_file, certificate_password)
    cert = pkcs12.get_certificate()
    der = b64encode(crypto.dump_certificate(
        crypto.FILETYPE_ASN1,
        cert)).decode("utf-8", "ignore")

    return {
        'Created': Created,
        'Expires': Expires,
        'Id': uuid4(),
        'BinarySecurityToken': der}


def get_xml_soap_with_signature(
        xml_soap_without_signature,
        Id,
        certificate_file,
        certificate_password):
    wsse = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"
    wsu = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd"
    X509v3 = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-x509-token-profile-1.0#X509v3"
    parser = etree.XMLParser(remove_blank_text=True)
    root = etree.fromstring(xml_soap_without_signature, parser=parser)
    signature_id = "{}".format(Id)
    signature = xmlsig.template.create(
        xmlsig.constants.TransformExclC14N,
        xmlsig.constants.TransformRsaSha256,#solo me ha funcionado con esta
        "SIG-" + signature_id)
    ref = xmlsig.template.add_reference(
        signature,
        xmlsig.constants.TransformSha256,
        uri="#id-" + signature_id)
    xmlsig.template.add_transform(
        ref,
        xmlsig.constants.TransformExclC14N)
    ki = xmlsig.template.ensure_key_info(
        signature,
        name="KI-" + signature_id)
    ctx = xmlsig.SignatureContext()
    ctx.load_pkcs12(get_pkcs12(certificate_file, certificate_password))

    for element in root.iter("{%s}Security" % wsse):
        element.append(signature)

    ki_str = etree.SubElement(
        ki,
        "{%s}SecurityTokenReference" % wsse)
    ki_str.attrib["{%s}Id" % wsu] = "STR-" + signature_id
    ki_str_reference = etree.SubElement(
        ki_str,
        "{%s}Reference" % wsse)
    ki_str_reference.attrib['URI'] = "#X509-" + signature_id
    ki_str_reference.attrib['ValueType'] = X509v3
    ctx.sign(signature)
    ctx.verify(signature)

    return root

def get_qr_code(data):
    qr = QRCode(
        version=1,
        error_correction=constants.ERROR_CORRECT_L,
        box_size=20,
        border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image()
    #temp = StringIO()
    temp = BytesIO()
    img.save(temp, format="PNG")
    qr_img = b64encode(temp.getvalue()).decode("utf-8", "ignore")


    return qr_img
