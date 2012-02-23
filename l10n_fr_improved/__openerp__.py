# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
##############################################################################
{
    'name': 'l10n_fr_improved',
    'version': '0.1',
    'category': 'Tools',
    'description': """
Improve l10n_fr module to fix main tax and trouble
    """,
    'author': 'Camptocamp',
    'website': 'http://openerp.camptocamp.com',
    'depends': ['l10n_fr'],
    'init_xml': [],
    'update_xml': ['taxe_codes.xml',
                   'account_type.xml',
                   'chart.xml',
                   'taxes.xml',
                   'fiscal_positions.xml'],
    'demo_xml': [],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
