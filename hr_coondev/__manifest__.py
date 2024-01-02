# -*- coding: utf-8 -*-
#########################################################################################################################
#
# Odoo Dev: Luis Felipe Paternina - lfpaternina93@gmail.com
#
# Odoo Funcional: Julian Bocanegra
#
# Bogotá, Colombia
#
########################################################################################################################

{
    'name': "HR Comfer",

    'summary': "Heredar modulos de RRHH",

    'description': "Este modulo instala funciones y campos adicionales en los modulos de RRHH",

    'author': "Luis Felipe Paternina",

    'contributors': ['Julian Bocanegra lp@todoo.co'],

    'website': "none",

    'category': 'RRHH',

    'version': '13',

        'depends': ['base',
        'hr',
        'contacts',
        'hr_payroll',
        'hr_payroll_account', 

        ],
    
    'data': [       
         'views/hr_employee.xml',
         'views/res_partner.xml',
         'views/hr_salary_rule.xml',
         'views/hr_contract.xml',
    ],
    
    'demo': [
        'demo/demo.xml',
    ],
}
