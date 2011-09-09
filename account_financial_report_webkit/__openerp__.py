# -*- encoding: utf-8 -*-
##############################################################################
#
#    Authors: Nicolas Bessi, Guewen Baconnier
#    Copyright Camptocamp SA 2011
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# TODO refactor helper in order to act more like mixin
# By using properties we will have a more simple signature in fuctions
{
    'name': 'Webkit based extended report financial report',
    'description': """

 - General Ledger
     Accounting > Reporting > Legal Reports > Accounting Reports > General Ledger Webkit
     With an option "Centralized" on accounts to group entries per period on the report.

 - Partner Ledger
     Accounting > Reporting > Legal Reports > Accounting Reports > Partner Ledger Webkit

Forthcoming :
 - Trial Balance
 - Partner Balance
 - Aged Partner Balance


Note : html headers and footers are deactivated for these reports because of an issue of wkhtmltopdf : http://code.google.com/p/wkhtmltopdf/issues/detail?id=656
       Instead, the header and footer are created as text with arguments passed to wkhtmltopdf. The texts are defined inside the report classes.

This module depends of the pending merge : https://code.launchpad.net/~c2c/openobject-addons/6.0-webkit-improvements/+merge/66428
This merge add the ability to pass dynamically values to html headers and footers.

""",
    'version': '1.0',
    'author': 'Camptocamp',
    'category': 'Finance',
    'website': 'http://www.camptocamp.com',

    'depends': ['account',
                'report_webkit'],
    'init_xml': [],
    'demo_xml' : [],
    'update_xml': ['account_view.xml',
                   'account_move_line_view.xml',
                   'data/financial_webkit_header.xml',
                   'report/report.xml',
                   'wizard/wizard.xml',
                   'wizard/account_report_general_ledger_wizard_view.xml',
                   'wizard/account_report_partners_ledger_wizard_view.xml'],
    # tests order matter
    'test': ['tests/general_ledger.yml'],
    #'tests/account_move_line.yml'
    'active': False,
    'installable': True,
}
