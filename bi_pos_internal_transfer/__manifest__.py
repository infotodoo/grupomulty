# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name" : "POS Internal Transfer in Odoo",
    "version" : "13.0.0.1",
    "category" : "Point of Sale",
    "depends" : ['base','sale_management','point_of_sale'],
    "author": "BrowseInfo",
    'summary': 'apps POS Transfer pos internal picking from point of sales stock internal transfer pos warehouse transfer pos item transfer pos picking transfer pos stock transfer pos stock internal transfer pos picking pos stock move pos product stock move from pos',
    "description": """
    
    Purpose :- 
    point of sales stock internal transfer pos warehouse transfer pos 
    point of sale warehouse transfer point of sales
    pos stock internal transfer
    stock internal transfer in POS
    stock transfer in POS
    internal picking transfer
    pos picking transfer
    pos stock transfer 
    pos item transfer
    stock transfer in pos

    picking internal transfer
This odoo apps help to register Internal Stock Transfer directly from point of sales in Odoo. Warehouse internal transfer is very important to every business, when you use the  POS and want to transfer stock via internal transfer operation for inventory then you can only do that from the backend using default Odoo process. But this Odoo apps module helps this stock internal transfer easily from the point of sales screen , after installing this module  no need to go back to backend menu you can easily transfer stock from one warehouse location to another stock location from the same point of sale screen.
POS Internal Transfer pos stock transfer pos Warehouse transfer pos
point of sale Internal Transfer point of sale stock transfer point of sale Warehouse transfer point of sales
point of sales Internal Transfer point of sales stock transfer point of sales Warehouse transfer

             This Module allow us to Transfer internal picking directly from point of sale.
    
    """,
    "website" : "https://www.browseinfo.in",
    'price': 15,
    'currency': "EUR",
    "data": [
        'views/POS_config_internal_transfer.xml'
    ],
    'qweb': [
        'static/src/xml/pos_internal_transfer.xml',
    ],
    "auto_install": False,
    "installable": True,
    "live_test_url": "https://youtu.be/L4Blbd5m9JQ",
    "images":['static/description/Banner.png'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
