# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.
{
    "name" : "Ajustes de Cuentas Analiticas",
    "author" : "Coondev",
    "version":"14.0.1",
    "depends" : ['stock', "base","sale"],
    "data": [
        'views/stock_picking.xml',
        #'security/ir.model.access.csv',
    ],
    "images": ["static/description/icon.png",],
    "application": True,
    "auto_install":False,
    "installable" : True,
    "currency": "COP"
}
