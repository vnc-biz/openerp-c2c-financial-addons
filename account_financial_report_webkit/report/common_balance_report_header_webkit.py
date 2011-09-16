# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright Camptocamp SA 2011
#    SQL inspired from OpenERP original code
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
from operator import add

from common_report_header_webkit import CommonReportHeaderWebkit
from tools.translate import _


class CommonBalanceReportHeaderWebkit(CommonReportHeaderWebkit):
    """Define common helper for balance (trial balance, P&L, BS oriented financial report"""

    def _get_account_details(self, account_ids, target_move, init_balance, fiscalyear, main_filter, start, stop, context=None):
        """
        Get details of accounts to display on the report
        @param account_ids: ids of accounts to get details
        @param target_move: selection filter for moves (all or posted)
        @param fiscalyear: browse of the fiscalyear
        @param main_filter: selection filter period / date or none
        @param start: start date or start period browse instance
        @param stop: stop date or stop period browse instance
        @param context: context container
        @return: dict of list containing accounts details, keys are the account ids
        """
        if context is None:
            context = {}
        account_obj = self.pool.get('account.account')
        ctx = context.copy()
        ctx.update({
            'state': target_move,
        })
        if fiscalyear:
            ctx.update({
                'fiscalyear': fiscalyear.id,
            })
        if main_filter in 'filter_period':
            ctx.update({
                'period_from': start.id,
                'period_to': stop.id
            })
        elif main_filter == 'filter_date':
            ctx.update({
                'date_from': start,
                'date_to': stop
            })

        accounts = account_obj.read(self.cr, self.uid, account_ids, ['type','code','name','debit','credit', 'balance', 'parent_id','level','child_id'], ctx)

        if init_balance:
            init_balance = self._compute_initial_balances(account_ids, start, fiscalyear, main_filter)

        accounts_by_id = {}
        for account in accounts:
            if init_balance:
                # sum for top level views accounts
                child_ids = account_obj._get_children_and_consol(self.cr, self.uid, account['id'], ctx)
                if child_ids:
                    child_init_balances = [init_bal['init_balance'] for acnt_id, init_bal in init_balance.iteritems() if acnt_id in child_ids ]
                    top_init_balance = reduce(add, child_init_balances)
                    account['init_balance'] = top_init_balance
                else:
                    account.update(init_balance[account['id']])
                account['balance'] = account['init_balance'] + account['debit'] - account['credit']
            accounts_by_id[account['id']] = account

        return accounts_by_id

    def _get_comparison_details(self, data, account_ids, target_move, comparison_filter, index):
        """

        @param data: data of the wizard form
        @param account_ids: ids of the accounts to get details
        @param comparison_filter: selected filter on the form for the comparison (filter_no, filter_year, filter_period, filter_date)
        @param index: index of the fields to get (ie. comp1_fiscalyear_id where 1 is the index)
        @return: dict of account details (key = account id)
        """
        fiscalyear = self._get_info(data, "comp%s_fiscalyear_id" % (index,), 'account.fiscalyear')
        start_period = self._get_info(data, "comp%s_period_from" % (index,), 'account.period')
        stop_period = self._get_info(data, "comp%s_period_to" % (index,), 'account.period')
        start_date = self._get_form_param("comp%s_date_from" % (index,), data)
        stop_date = self._get_form_param("comp%s_date_to" % (index,), data)

        accounts_by_ids = {}
        comp_params = {}
        if comparison_filter != 'filter_no':
            details_filter = comparison_filter
            if comparison_filter == 'filter_year':
                start = self.get_first_fiscalyear_period(fiscalyear)
                stop = self.get_last_fiscalyear_period(fiscalyear)
                details_filter = 'filter_period'  # same behavior as filter periods
            elif comparison_filter == 'filter_date':
                start = start_date
                stop = stop_date
            else:
                start = start_period
                stop = stop_period

            accounts_by_ids = self._get_account_details(account_ids, target_move, False,
                                                        fiscalyear, details_filter,
                                                        start, stop)
            comp_params = {
                'comparison_filter': comparison_filter,
                'fiscalyear': fiscalyear,
                'start': start,
                'stop': stop,
            }

        return accounts_by_ids, comp_params
