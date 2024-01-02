# -*- coding: utf-8 -*-
##########################################################################################################
#
#
#
#########################################################################################################

{
    'name': 'Sales Orders Approval',

    'version': '14.0',

    'category': 'Sales',

    'author': 'Luis Felipe Paternina',

    'summary': 'Sales Orders Approval',

    'description': """Manage sales quotations and orders Approval.""",

    'license': 'LGPL-3',

    'depends': ['base_setup','sale', 'sales_team'],
    'images': ['static/description/icon.png'],

    'data': [
        'views/res_user_views.xml',
        'views/sale_order.xml',
        'views/sale_approvals_settings.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
    ],

    'installable': True,
    'auto_install': False,
    'application': True,
}
