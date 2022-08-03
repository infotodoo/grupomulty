# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

import logging
_logger = logging.getLogger(__name__)


class ElectronicInvoiceFunctions(http.Controller):

    @http.route('/approve-electronic-invoice/<string:token_id>/<string:rating>', type='http', auth='none')
    def approve_fe(self, token_id, rating, **kwargs):
        assert rating in ('True', 'False'), "Aprobación de Factura Erronea"
        invoice_id = request.env['account.move'].sudo().search([('approve_token', '=', token_id),], limit=1)
        if not invoice_id:
            return request.not_found()

        if invoice_id.invoice_rating != 'not_rating':
            return request.render('l10n_co_e_invoicing.invoice_rating_refuse', {
                'rating': invoice_id.invoice_rating,
                'invoice': invoice_id,
                'token': token_id,
            })

        if rating == 'True':
            rating_system = 'aprobada'
            invoice_id.write({'invoice_rating': 'approve'})
        elif rating == 'False':
            rating_system = 'rechazada'
            invoice_id.write({'invoice_rating': 'refuse'})
        else:
            return request.render('l10n_co_e_invoicing.invoice_rating_refuse', {
                'rating': 'Valide el valor de aprobacion enviado',
                'invoice': invoice_id,
                'token': token_id,
            })

        if rating == 'True':
            invoice_id.dian_document_lines.sudo().express_acceptation()

        return request.render('l10n_co_e_invoicing.approve_electronic_invoice_messages', {
            'rating': rating_system,
            'invoice': invoice_id,
            'token': token_id,
        })

    @http.route(['/approve-electronic-invoice/<string:token_id>/refund_text'], type="http", auth="public", methods=['post'])
    def feedback_fe(self, token_id, **kwargs):
        invoice_id = request.env['account.move'].sudo().search([('approve_token', '=', token_id)], limit=1)
        if not invoice_id:
            return request.not_found()
        invoice_id.write({'refuse_text': kwargs.get('refund_text')})
        return request.render('l10n_co_e_invoicing.electronic_invoice_notification_refuse', {'web_base_url': request.env['ir.config_parameter'].sudo().get_param('web.base.url'),'invoice': invoice_id,})
