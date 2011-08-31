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
from tools.translate import _
import pooler

from common_report_header_webkit import CommonReportHeaderWebkit


class GeneralLedgerWebkit(report_sxw.rml_parse, CommonReportHeaderWebkit):

    def __init__(self, cursor, uid, name, context):
        super(GeneralLedgerWebkit, self).__init__(cursor, uid, name, context=context)
        self.pool = pooler.get_pool(self.cr.dbname)
        self.cursor = self.cr
        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name': _('General Ledger'),
            'display_account': self._get_display_account,
            'display_account_raw': self._get_display_account_raw,
            'filter': self._get_filter,
            'target_move': self._get_target_move,
            'initial_balance': self._get_initial_balance,
            'amount_currency': self._get_amount_currency,
        })

    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each browse record that will be used
        by mako template"""
        new_ids = data['form']['account_ids'] or data['form']['chart_account_id']

        # We memoize ledger lines linked to account. Key is account id
        # values are array of lines
        ledger_lines_memoizer = {}

        # Account initial balance memoizer
        init_balance_memoizer = {}

        # Reading form
        init_bal = self._get_form_param('initial_balance', data)
        main_filter = self._get_form_param('filter', data, default='filter_no')
        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        fiscalyear = self.get_fiscalyear_br(data)

        if main_filter == 'filter_no':
            start_period = self.get_first_fiscalyear_period(fiscalyear)
            stop_period = self.get_last_fiscalyear_period(fiscalyear)

        # Retrieving accounts
        accounts = self.get_all_accounts(new_ids, filter_view=True, filter_hidden=True)
        if init_bal and main_filter in ('filter_no', 'filter_period'):
            init_balance_memoizer = self._compute_inital_balances(accounts, start_period,
                                                                  fiscalyear, main_filter)

        # computation of ledeger lines
        if main_filter == 'filter_date':
            start = start_date
            stop = stop_date
        else:
            start = start_period
            stop = stop_period
        ledger_lines_memoizer = self._compute_account_ledger_lines(accounts, init_balance_memoizer,
                                                                   main_filter, target_move, start, stop)
        objects = []
        for account in self.pool.get('account.account').browse(self.cursor, self.uid, accounts):
            account.ledger_lines = ledger_lines_memoizer.get(account.id, [])
            account.init_balance = init_balance_memoizer.get(account.id, {})
            objects.append(account)
        return super(GeneralLedgerWebkit, self).set_context(objects, data, new_ids,
                                                            report_type=report_type)

    def _compute_account_ledger_lines(self, accounts_ids, init_balance_memoizer, main_filter,
                                      target_move, start, stop):
        res = {}
        valid_only = True
        if target_move == 'all':
            valid_only = False
        for acc_id in accounts_ids:
            # We get the move line ids of the account depending of the
            # way the initial balance was created we include or not opening entries
            search_mode = 'include_opening'
            if acc_id in init_balance_memoizer:
                if init_balance_memoizer[acc_id].get('state') == 'read':
                    search_mode = 'exclude_opening'
            move_line_ids = self.get_move_lines_ids(acc_id, main_filter, start, stop,
                                                    mode=search_mode, valid_only=valid_only)
            if not move_line_ids:
                res[acc_id] = []
                continue
            lines = self._get_ledger_lines(move_line_ids, acc_id)
            res[acc_id] = lines
        return res

    def _get_ledger_lines(self, move_line_ids, account_id):
        if not move_line_ids:
            return []
        res = self._get_move_line_datas(move_line_ids)
        ## computing counter part is really heavy in term of ressouces consuption
        ## looking for a king of SQL to help me improve it
        move_ids = [x.get('move_id') for x in res]
        counter_parts = self._get_moves_counterparts(move_ids, account_id)
        for line in res:
            line['counterparts'] = counter_parts.get(line.get('move_id'), '')
        return res


report_sxw.report_sxw('report.account.account_report_general_ledger_webkit',
                      'account.account',
                      'addons/account_financial_report_webkit/report/templates/account_report_general_ledger.mako',
                      parser=GeneralLedgerWebkit)
