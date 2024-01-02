# -*- coding: utf-8 -*-
{
    'name': 'Configuraciones de Apicom',
    'version': '14.0',
    'category': 'Sales',
    'author': 'Coondev - Daniers D.',
    'description': """Manage sales quotations and orders Approval.""",
    'license': 'LGPL-3',
    'depends': ['base','sale', 'stock', 'sales_team', 'sale_stock_renting'],
    'images': ['static/description/icon.png'],
    'data': [
        'reports/purchase_report_templates.xml',
        'views/res_company.xml',
        'views/stock_warehouse.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml'
             ],
    'qweb': [
        'static/src/xml/activity.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
