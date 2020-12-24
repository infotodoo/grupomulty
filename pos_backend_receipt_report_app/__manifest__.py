# -*- coding: utf-8 -*-

{
    'name' : 'POS Backend Receipt Report Odoo',
    'author': "Edge Technologies",
    'version' : '13.0.1.0',
    'live_test_url':'https://youtu.be/riX0PrgH1dc',
    "images":['static/description/main_screenshot.png'],
    'summary' :'App Print POS backend receipt point of sale backend receipt point of sales backend receipt pos receipt report point of sale receipt report point of sales receipt report Generate receipt from POS customer receipt send POS receipt print point of sale receipt',
    'description' : """
        This module is useful for generate receipt and you can send receipt to the customer.
    """,
    "license" : "OPL-1",
    'depends' : ['point_of_sale','mail'],
    'data': [
            'report/receipt_report.xml',
            'report/receipt_template.xml',
            'report/email_template.xml',
            'views/pos_inherit.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable' : True,
    'auto_install' : False,
    'price': 18,
    'currency': "EUR",
    "category" : "Point of Sales",
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
