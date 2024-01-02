{
    'name': 'Sale order Sannic',

    'version': '14',

    'author': "Luis Felipe Paternina",

    'website': "",

    'category': 'learning',

    'depends': [
        'base',
        'sale_management',
        'crm',
        'sale_margin',
        'sale_approval_co'
    ],

    'data': [

        'views/sale_order.xml',
        'views/crm_lead.xml',
        'views/sale_order_freigth.xml',
        'views/purchase_order.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
              
    ],
    'installable': True
}