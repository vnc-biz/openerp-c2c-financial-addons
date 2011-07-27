# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
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
{
    'name': 'Webkit based extended report financial report',
    'description': """TODO""",
    'version': '1.0',
    'author': 'Camptocamp SA',
    'category': 'Accounting',
    'website': 'http://www.camptocamp.com',

    'depends': ['account',
                'report_webkit'],
    'init_xml': [],
    'demo_xml' : [],
    'update_xml': ['account_move_line_view.xml',
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
