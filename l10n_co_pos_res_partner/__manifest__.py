# -*- coding: utf-8 -*-
###############################################################################
#                                                                             #
#                                                                             #
# Part of Odoo. See LICENSE file for full copyright and licensing details.    #
#                                                                             #
#                                                                             #
#                                                                             #
# Co-Authors    Odoo LoCo                                                     #
#               Localización funcional de Odoo para Colombia                  #
#                                                                             #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU Affero General Public License as published by #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU Affero General Public License for more details.                         #
#                                                                             #
# You should have received a copy of the GNU Affero General Public License    #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
###############################################################################

{
    'name': 'Colombia - res partner',
    'category': 'Localization',
    'version': '13.0',
    'author': 'Diego Carvajal',
    'license': 'AGPL-3',
    'maintainer': 'Dracosoft',
    'website': 'https://dracosoft.com.co',
    'summary': ' ',
    'description': """
Colombia Point of Sale:
======================
  """,
    'depends': [
        'point_of_sale'
    ],
    'data': [
        'views/pos_view.xml',
    ],
    'qweb': ['static/src/xml/*.xml'],
    'installable': True,
}
