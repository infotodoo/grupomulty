# -*- coding: utf-8 -*-

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalAccount(CustomerPortal):

    @http.route(['/my/loyalty/history/<int:partner_id>'], type='http', auth="public", website=True)
    def portal_my_loyalty_history(self, partner_id, access_token=None, report_type=None, download=False, **kw):
        partner = request.env['res.partner'].browse(int(partner_id))
        try:
            if any(request.env.user.has_group('sales_team.group_sale_manager') for u in partner.user_ids if u != request.env.user) or any(u == request.env.user for u in partner.user_ids):
                partner = self._document_check_access('res.partner', partner_id)
            else:
                raise AccessError(_("Only sale manager can see other partner's loyalty history !"))
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(model=partner, report_type=report_type, report_ref='sale_loyalty.loyalty_points_history', download=download)
