# -*- coding: utf-8 -*-
# Copyright 2019 Diego Carvajal <Github@diegoivanc>
# Copyright 2019 Joan Marín <Github@joanmarin>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Colombian E-Invoicing",
    "category": "Financial",
    "version": "14.0",
    "author": "Diego Carvajal Github@diegoivanc,"
              "EXA Auto Parts Github@exaap, "
              "Joan Marín Github@joanmarin"
              "Bernardo D. Lara bl@todoo.co",
    "website": "http://www.dracosoft.com.co",
    "license": "AGPL-3",
    "summary": "Colombian E-Invoicing",
    "depends": ['base',"l10n_co_dian_data",'sale','purchase','sales_team'],
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
        "report/account_invoice_report_template.xml",
        "report/account_move_reports.xml",
        "report/account_move_templates.xml",
        "data/product_scheme_data.xml",
    ],
    "installable": True,
}
