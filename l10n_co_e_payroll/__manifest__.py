# -*- coding: utf-8 -*-
# Copyright 2023 Diego Carvajal <Github@diegoivanc>
{
    "name": "Colombian E-Payroll",
    "category": "Financial",
    "version": "16.0.1",
    "author": "Diego Carvajal Github@diegoivanc",
    "website": "https://www.dracosoft.com.co",
    'license': 'OPL-1',
    "summary": "Colombian E-Payroll",
    "depends": ["account"],
    'external_dependencies': {
        'python': [
            'validators',
            'OpenSSL',
            'xades',
        ],
    },
    "data": [
        "views/res_company_views.xml",
        "views/payroll_views.xml",

    ],
    "installable": True,
}
