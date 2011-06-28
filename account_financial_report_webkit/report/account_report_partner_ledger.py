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

import time

from report import report_sxw
from osv import osv
import pooler

from common_report_header_webkit import CommonReportHeaderWebkit

class GeneralLedgerWebkit(report_sxw.rml_parse, CommonReportHeaderWebkit):
    

    def __init__(self, cursor, uid, name, context):
        super(GeneralLedgerWebkit, self).__init__(cursor, uid, name, context=context)
        self.pool = pooler.get_pool(self.cr.dbname)
        self.cursor = self.cr
        
        self.localcontext.update({
            'cr':cursor,
            'uid': uid,
        })
        
    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each browse record that will be used 
        by mako template"""
        new_ids = data['form']['chart_account_id']
         
        # We memoize ledger lines linked to account key is account id
        # values array of lines
        ledger_lines_memoizer = {}
        # Account initial balance memoizer
        init_balance_memoizer = {}
        import pprint
        pprint.pprint(data)
        init_bal = data.get('form', {}).get('initial_balance')
        filter = data.get('form', {}).get('filter', 'filter_no')
        
        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        fiscalyear = self.get_fiscalyear_br(data)
        if filter == 'filter_no':
            start_period = self.get_first_fiscalyear_period(fiscalyear)
            stop_period = self.get_last_fiscalyear_period(fiscalyear)
        accounts =  self.get_all_accounts(new_ids, filter_view=True)
        if init_bal and filter in ('filter_no', 'filter_period'):
            init_balance_memoizer = self._compute_inital_balances(accounts, start_period, 
                                                                  fiscalyear, filter)
        objects = []
        for account in self.pool.get('account.account').browse(self.cursor, self.uid, accounts):
            account.ledger_lines = init_balance_memoizer.get(account.id, {})
            objects.append(account)
        return super(GeneralLedgerWebkit, self).set_context(objects, data, new_ids,
                                                            report_type=report_type)
                                                            
    def _compute_account_ledger_lines(self, accounts_ids, init_balance_memoizer, filter, 
                                      data, start, stop):
        res = {}
        for acc_id in accounts_ids:
            # We get the move line ids of the account depending of the 
            # way the initial balance was created we include or not opening entries
            search_mode = 'include_special'
            if acc_id in init_balance_memoizer:
                if init_balance_memoizer[acc_id].get('state') == 'read':
                    search_mode = 'exclude_special'


        
report_sxw.report_sxw('report.account.account_report_partner_ledger_webkit',
                      'account.account', 
                      'addons/account_financial_report_webkit/report/templates/account_report_partner_ledger.mako',
                      parser=GeneralLedgerWebkit)
