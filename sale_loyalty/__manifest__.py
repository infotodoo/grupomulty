# -*- coding: utf-8 -*-
#################################################################################
# Author      : Kanak Infosystems LLP. (<https://www.kanakinfosystems.com/>)
# Copyright(c): 2012-Present Kanak Infosystems LLP.
# All Rights Reserved.
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://www.kanakinfosystems.com/license>
#################################################################################
{
    'name': 'Sale Loyalty',
    'version': '2.0',
    'category': 'Sales/Sales',
    'summary': 'Loyalty Points on Sale Order',
    'description': """
        Loyalty Points and Rewards on Sale Order
    """,
    'license': 'OPL-1',
    'author': 'Kanak Infosystems LLP.',
    'website': 'https://www.kanakinfosystems.com',
    'depends': ['sale_management'],
    'data': [
        'security/sale_loyalty_security.xml',
        'security/ir.model.access.csv',
        'data/sale_loyalty_data.xml',
        'views/sale_loyalty_views.xml',
        'views/res_config_view.xml',
        'views/sale_view.xml',
        'views/sale_portal_template.xml',
        'views/sale_loyalty_history_views.xml',
        'views/res_partner.xml',
        'report/sale_report.xml',
        'report/points_history_report.xml',
        'wizard/point_selection_wizard_view.xml'
    ],
    'images': ['static/description/banner.jpg'],
    'sequence': 1,
    'installable': True,
    'application': True,
    'auto_install': False,
    'price': 50,
    'currency': 'EUR',
    'live_test_url': 'https://youtu.be/FUZtxA8MuXE',
}
