# -*- coding: utf-8 -*-
# Copyright 2019 Joan Marín <Github@joanmarin>
# Copyright 2019 Diego Carvajal <Github@diegoivanc>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Modificación de Reporte de FE",
    "category": "Financial",
    "version": "14.0.1.0.0",
    "author": "Coondev - Michael D. Colorado",
    "website": "http://www.Coondev.com",
    "license": "AGPL-3",
    "summary": "Colombian E-Invoicing",
    "depends": ["l10n_co_e_invoicing"],
    'external_dependencies': {
        'python': [
            'validators',
            'OpenSSL',
            'xades',
        ],
    },
    "data": [
        "report/account_move_templates.xml"
    ],
    "installable": True,
}
