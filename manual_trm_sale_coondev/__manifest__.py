# -*- coding: utf-8 -*-

# Part of Daniers C. See LICENSE file for full copyright and licensing details.

{
    'name': 'TRM manual en lineas de ventas y compras',
    'version': '14',
    'author': "Coondev - Daniers C",
    'website': "www.coondev.com",
    'category': 'Sales',
    'license': 'OPL-1',
    'images': ['static/description/icon.png'],
    'depends': [
        'base',
        'crm',
        'sale',
        'sales_order_vendor_po'
    ],

    'data': [
        'views/sale_order.xml',
        'views/purchase_order.xml',
    ],
    'installable': True
}