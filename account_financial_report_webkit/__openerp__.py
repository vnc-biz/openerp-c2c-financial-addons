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
This module will provide with basic legal financial reports. All report uses the webkit technology and the library 'wkhtmltopdf' for the pdf rendering. (this library path must be added to you company settings)

The reports provided are:

* The General leder: details of all entries posted in your books sorted by account.
    - Filter by account in the wizard (no need to go to the Chart of account to do this anymore) or by view account (the report will display all regular children account) ie: you can select all P&L accounts.
    - The report will now print only account with movements OR with a balance not null. No more endless report with accounts with no data. (field: display account is hidden)
    - Correct opening balance calculation : even if you do not have created your opening entries yet. If you did so, system will simply uses your opening entries amounts otherwise it will be calculated backwards until the last opening entries posted. (it remains important to post opening entries if you do not want to loose performance but with few data it is not mandatory anymore)
    - Reports now show cumulative balances
    - You can filter, for exemple from the 02/2011 to 06/2011 with an opening balance that will includes not only previous years data but also data from begining of  fiscal year until the period start of your filter ; so you will always match with your trial balance.
    - Thanks to a new checkbox in account form, you will have possibility to centralize any accounts you like. ie: you do not want to see all entries posted under the account 'VAT on sales' ; you will only see aggregated amounts by periods. This option can save hundreds of useless pages !
    - User name added on foot page (+ date, time, page of course)
    - Counterpart account displayed for each transaction (3 accounts max.) to ease searching.
    - Better ergonomy on the wizard: important information at the top, filters in the middle, options at the bottom, more specific filtering on a different tab. No more unique wizard layout for all financial reports (ie: we have removed the journal tab useless for the GL report)
    - And obviously an improved style

 * The partner ledger: details of entries relative to payable & receivable accounts posted in your books sorted by account and partner.
    - Filter by partner now possible
    - Possibility to print unreconcilied transactions only at any date in the past (thanks to the brand-new field: last_rec_date which calculated the last move line reconciled date). No more pain to get open invoices at the last closing date.
    - Now you can see accounts then Partner with subtotals for each account allowing you to check you data with trial balance and partner balance for instance & accounts are ordered the same way than in the Chart of account
    - period have been added (date only is uncompleted)
    - Reconciliation mark added
    - same as GL report: The report will now print only account with movements OR with a balance not null. No more endless report with accounts with no data. (field: display account is hidden)
    - same as GL report: opening balance is fully calculated ; no need to generate opening entry anymore
    - same as GL report: Reports now show cumulative balances
    - same as GL report: You can filter, for example from the 02/2011 to 06/2011 with an opening balance that will includes not only previous years data but also data from beginning of  fiscal year until the period start of your filter ; so you will always match with your trial balance.
    - same as GL report: User name added on foot page (+ date, time, page of course)
    - same as GL report: Better ergonomy on the wizard
    - And an improved style


 * The Trial balance: still to be added

 * The Partner balance: still to be added

 * A printscreen of the entries selected: still to be added

 * A printscreen of invoices selected: still to be added


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
                   'wizard/account_report_partners_ledger_wizard_view.xml',
                   'wizard/account_report_trial_balance_wizard_view.xml',
                   ],
    # tests order matter
    'test': ['tests/general_ledger.yml'],
    #'tests/account_move_line.yml'
    'active': False,
    'installable': True,
}
