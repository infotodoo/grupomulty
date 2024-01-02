# -*- coding: utf-8 -*-
{
    'name': "Sale Order Vendor PO",

    'version': '2.2.0',

    'category': 'Sales',

    'license': 'Other proprietary',

    'summary': """Select vendor for PO on sales order lines""",

    'description': """Select vendor for PO on sales order lines""",

    'author': '',

    'website': "https://www.flexerp.dk/",

    'license': 'OPL-1',

    'images': ['static/description/sales_order.png'],
    'depends': [
        'sale_purchase',
        'stock',
        'sale_stock',
        'sale_margin',
        'sale_order_sannic',
    ],
    'data':[
        'views/sale_order_view.xml',
        'views/product_product.xml',
        'views/product_template.xml',
        'reports/purchase_report.xml',
        'security/ir.model.access.csv',
    ],
    'installable' : True,
    'application' : False,
    'auto_install' : False,
}
