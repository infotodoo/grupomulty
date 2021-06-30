# -*- coding: utf-8 -*-
{
    'name': "SABANAS DE DATOS",

    'summary': "SABANAS DE DATOS",

    'description': "SABANAS DE DATOS",

    'author': "Todoo SAS",
    'contributors': "Livingston Arias Narváez la@todoo.co",
    'website': "http://www.todoo.co",
    'category': 'Accounting',
    'version': '13.1',

    # any module necessary for this one to work correctly
    'depends': ['account','sale','report_multi','l10n_co_dian_data'],
  
    # always loaded
    'data': [
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
        'views/purchase_order_view.xml',
        'views/account_move_view.xml',
        'security/ir.model.access.csv',
        'views/report_view.xml',
        'views/menuitem.xml',
    ],
}