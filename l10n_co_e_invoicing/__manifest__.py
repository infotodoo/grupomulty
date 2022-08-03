# -*- coding: utf-8 -*-
# Copyright 2021 Diego Carvajal <Github@diegoivanc>

{
    "name": "Colombian E-Invoicing",
    "category": "Financial",
    "version": "14.0",
    "author": "Diego Carvajal Github@diegoivanc,",
    "website": "http://www.dracosoft.com.co",
    'license': 'OPL-1',
    "summary": "Colombian E-Invoicing",
    "depends": ["l10n_co_dian_data",],
    'external_dependencies': {
        'python': [
            'validators',
            'OpenSSL',
            'xades',
        ],
    },
    "data": [
        'security/ir.model.access.csv',
        "views/account_invoice_views.xml",
        "views/account_invoice_dian_document_views.xml",
        "views/account_journal_views.xml",
        "views/ir_sequence_views.xml",
        "views/res_company_views.xml",
        "views/account_tax_group_views.xml",
        "views/product_template_views.xml",
        "views/account_move_approve.xml",
        "report/account_invoice_report_template.xml",
        "report/account_move_reports.xml",
        "report/account_move_templates.xml",
        "data/product_scheme_data.xml",
        "data/cron_acp_tacita_dian.xml",
    ],
    "installable": True,
}
