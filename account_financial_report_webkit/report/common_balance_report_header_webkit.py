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

    def _get_numbers_display(self, data):
        return self._get_form_param('numbers_display', data)

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
        init_balance = self.is_initial_balance_enabled(comparison_filter)

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

            accounts_by_ids = self._get_account_details(account_ids, target_move, init_balance,
                                                        fiscalyear, details_filter,
                                                        start, stop)
            comp_params = {
                'comparison_filter': comparison_filter,
                'fiscalyear': fiscalyear,
                'start': start,
                'stop': stop,
                'initial_balance': init_balance,
            }

        return accounts_by_ids, comp_params

    def is_initial_balance_enabled(self, main_filter):
        if main_filter not in ('filter_no', 'filter_year'):
            return False
        return True

    def _get_diff(self, balance, last_balance):
        """
        @param balance: current balance
        @param last_balance: last balance
        @return: dict of form {'diff': difference, 'percent_diff': diff in percentage}
        """
        diff = balance - last_balance
        percent_diff = 0.0

        obj_precision = self.pool.get('decimal.precision')
        precision = obj_precision.precision_get(self.cr, self.uid, 'Account')
        if last_balance == 0:
            percent_diff = False
        else:
            percent_diff = round(diff / last_balance * 100, precision)

        return {'diff': diff, 'percent_diff': percent_diff}

    def compute_balance_data(self, data, filter_report_type=None):
        new_ids = data['form']['account_ids'] or data['form']['chart_account_id']
        max_comparison = self._get_form_param('max_comparison', data, default=0)
        main_filter = self._get_form_param('filter', data, default='filter_no')

        comp_filters = []
        for index in range(max_comparison):
            comp_filters.append(self._get_form_param("comp%s_filter" % (index,), data, default='filter_no'))

        fiscalyear = self.get_fiscalyear_br(data)

        nb_comparisons = len([comp_filter for comp_filter in comp_filters if comp_filter != 'filter_no'])

        if not nb_comparisons:
            comparison_mode = 'no_comparison'
        elif nb_comparisons > 1:
            comparison_mode = 'multiple'
        else:
            comparison_mode = 'single'

        init_bal = self.is_initial_balance_enabled(main_filter)
        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        chart_account = self._get_chart_account_id_br(data)

        if main_filter == 'filter_no':
            start_period = self.get_first_fiscalyear_period(fiscalyear)
            stop_period = self.get_last_fiscalyear_period(fiscalyear)

        # Retrieving accounts
        account_ids = self.get_all_accounts(new_ids, filter_view=False, filter_report_type=filter_report_type)

        # computation of ledger lines
        if main_filter == 'filter_date':
            start = start_date
            stop = stop_date
        else:
            start = start_period
            stop = stop_period

        accounts_by_ids = self._get_account_details(account_ids, target_move, init_bal,
                                                    fiscalyear, main_filter, start, stop)

        comparison_params = []
        comp_accounts_by_ids = []
        for index in range(max_comparison):
            if comp_filters[index] != 'filter_no':
                comparison_result, comp_params = self._get_comparison_details(data, account_ids, target_move, comp_filters[index], index)
                comparison_params.append(comp_params)
                comp_accounts_by_ids.append(comparison_result)

        objects = []
        for account_id in account_ids:
            if not accounts_by_ids[account_id]['parent_id']:  # hide top level account
                continue
            accounts = {}
            accounts['current'] = accounts_by_ids[account_id]
            comp_accounts = []
            for comp_account_by_id in comp_accounts_by_ids:
                values = comp_account_by_id.get(account_id)
                values.update(self._get_diff(accounts['current']['balance'], values['balance']))
                comp_accounts.append(values)
            accounts['comparisons'] = comp_accounts
            objects.append(accounts)

        context_report_values = {
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'chart_account': chart_account,
            'comparison_mode': comparison_mode,
            'nb_comparison': nb_comparisons,
            'initial_balance': init_bal,
            'comp_params': comparison_params,
        }
        return objects, new_ids, context_report_values
