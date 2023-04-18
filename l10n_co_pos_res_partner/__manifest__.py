# -*- coding: utf-8 -*-
{
    'name': 'Colombia - res partner',
    'category': 'Localization',
    'version': '13.0',
    'author': 'Diego Carvajal',
    'license': 'OPL-1',
    'maintainer': 'Dracosoft',
    'website': 'https://dracosoft.com.co',
    'summary': ' ',
    'description': """
Colombia Point of Sale:
======================
  """,
    'depends': [
        'point_of_sale','stock','base','website','delivery'
    ],
    'data': [
        'security/res_groups.xml',
        'views/template.xml',
        'views/pos_view.xml',
        'views/res_partner.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
}
