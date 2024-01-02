# -*- coding: utf-8 -*-
{
    'name': "Historico de Actividades",
    'author': 'Coondev SAS - Daniers D',
    'category': 'Activity',
    'summary': """Activity history of the all system""",
    'license': 'AGPL-3',
    'website': 'http://www.coondev.com',
    'description': """
""",
    'version': '1.0',
    'depends': ['mail','crm'],
    'data': ['views/activity_history.xml',
             'security/groups.xml',
             'security/ir.model.access.csv'
            ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
