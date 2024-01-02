###############################################################################################
#
# Luis Felipe Paternina  - Julian Bocanegra - Daniers Diaz
# Odoo Dev                 Odoo Consulting
# 
# Bogotá,Colombia
#
#
###############################################################################################

{
    'name': 'Modificacion de Reportes de FE',
    'version': '14.0.0.0',
    'author': "Coondev S.A.S",
    'contributors': ['Luis Felipe Paternina','M. Daniers C. Diaz.'],
    'website': "www.coodev.com",
    'category': 'reports',
    'images': ['static/description/icon.png'],
    'depends': [

        'account_accountant',
        'base',
        'l10n_co_dian_data',
        'l10n_co_e_invoicing',
        'od_journal_sequence',
    ],
    'data': [
        'reports/invoice_report.xml',      
        'reports/pos_invoice_report.xml',
    ],
    'installable': True
}
