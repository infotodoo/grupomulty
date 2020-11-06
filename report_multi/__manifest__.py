{
    'name': 'Report_Multi',
    'version': '13',
    'author': "Todoo SAS",
    'website': "www.todoo.co",
    'category': 'Style',
    'depends': [
        'base',
        'contacts',
        'sale_management',
        'stock',
        'base_address_city',
    ],
    'data': [
        'security/ir.model.access.csv', 
        #Luis Felipe Paternina Vital     
        'views/res_partner.xml',
        'views/res_partner_zone.xml',
        'views/res_partner_type.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/product.xml',
        'views/stock_move.xml',

    ],
    'installable': True
}