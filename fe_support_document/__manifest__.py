# -*- coding: utf-8 -*-
{
    "name" : "Documento Soporte",
    "author" : "Coondev SAS",
    "email": 'soporte@coondev.com.co',
    "website":'https://coondev.odoo.com/',
    "version":"14.0.1",

    # any module necessary for this one to work correctly
    'depends': ['base','l10n_co_e_invoicing'],

    # always loaded
    'data': [
        "security/res_groups.xml",
        'security/ir.model.access.csv',
        'views/account_journal_views.xml',
        'views/account_invoice_views.xml',
    ],
    "application": True,
    "auto_install":False,
    "installable" : True,
    "currency": "COP"
}
