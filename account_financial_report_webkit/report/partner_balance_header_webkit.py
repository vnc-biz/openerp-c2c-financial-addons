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

from collections import defaultdict
from operator import add

from common_balance_report_header_webkit import CommonBalanceReportHeaderWebkit
from common_partners_report_header_webkit import CommonPartnersReportHeaderWebkit

from tools.translate import _


class CommonPartnerBalanceReportHeaderWebkit(CommonBalanceReportHeaderWebkit, CommonPartnersReportHeaderWebkit):
    """Define common helper for balance (trial balance, P&L, BS oriented financial report"""

    def _get_account_partners_details(self, account_ids, main_filter, fiscalyear, target_move, start,
                              stop, partner_filter_ids=False):
        res = {}
        valid_only = True if target_move == 'all' else False
        filter_from = False
        if main_filter in ('filter_period', 'filter_no'):
            filter_from = 'period'
        elif main_filter == 'filter_date':
            filter_from = 'date'
            
        partners_init_balances_by_ids = {}
        if self.is_initial_balance_enabled(main_filter):
            partners_init_balances_by_ids = self._compute_partners_initial_balances(account_ids,
                                                                                    start,
                                                                                    fiscalyear,
                                                                                    main_filter,
                                                                                    partner_filter=partner_filter_ids,
                                                                                    exclude_reconcile=False)

        for account_id in account_ids:
            details = self._get_partners_totals_account(filter_from,
                                                        account_id,
                                                        start,
                                                        stop,
                                                        valid_only=valid_only,
                                                        partner_filter_ids=partner_filter_ids)
            for partner_id, partner_details in details.iteritems():
                # merge partner credit / debit and initial balance
                if partners_init_balances_by_ids[account_id].get(partner_id):
                    details[partner_id] = dict(partner_details.items() +
                                               partners_init_balances_by_ids[account_id][partner_id].items())

                if not details[partner_id].get('init_balance'):
                    details[partner_id]['init_balance'] = 0.0

                details[partner_id]['balance'] = details[partner_id].get('init_balance', 0.0) +\
                                                 details[partner_id]['debit'] -\
                                                 details[partner_id]['credit']
            res[account_id] = details

        return res

    def _get_partners_totals_account(self, filter_from, account_id, start, stop, valid_only=False, partner_filter_ids=False):
        final_res = {}
        sql_select = """
                 SELECT partner_id,
                        sum(debit) AS debit,
                        sum(credit) AS credit
                 FROM account_move_line"""

        sql_where = "WHERE account_id = %(account_id)s "
        sql_conditions, search_params = getattr(self, '_get_query_params_from_'+filter_from+'s')(start, stop)
        sql_where += sql_conditions

        if partner_filter_ids:
            sql_where += "   AND partner_id in %(partner_ids)s"
            search_params.update({'partner_ids': tuple(partner_filter_ids),})
        if valid_only:
            sql_where += "   AND state = 'valid' "

        sql_groupby = "GROUP BY partner_id"

        search_params.update({'account_id': account_id,})
        query = ' '.join((sql_select, sql_where, sql_groupby))

        self.cursor.execute(query, search_params)
        res = self.cursor.dictfetchall()
        if res:
            for row in res:
                final_res[row['partner_id']] = row
        return final_res

    def _get_filter_type(self, result_selection):
        filter_type = ('payable', 'receivable')
        if result_selection == 'customer':
            filter_type = ('receivable',)
        if result_selection == 'supplier':
            filter_type = ('payable',)
        return filter_type

    def _get_partners_comparison_details(self, data, account_ids, target_move, comparison_filter, index, partner_filter_ids=False):
        """

        @param data: data of the wizard form
        @param account_ids: ids of the accounts to get details
        @param comparison_filter: selected filter on the form for the comparison (filter_no, filter_year, filter_period, filter_date)
        @param index: index of the fields to get (ie. comp1_fiscalyear_id where 1 is the index)
        @param partner_filter_ids: list of ids of partners to select
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
        accounts_details_by_ids = defaultdict(dict)
        if comparison_filter != 'filter_no':
            details_filter = comparison_filter
            if comparison_filter == 'filter_year':
                start = self.get_first_fiscalyear_period(fiscalyear)
                stop = self.get_last_fiscalyear_period(fiscalyear)
                details_filter = 'filter_no'
            elif comparison_filter == 'filter_date':
                start = start_date
                stop = stop_date
            else:
                start = start_period
                stop = stop_period

            accounts_by_ids = self._get_account_details(account_ids, target_move, init_balance,
                                                        fiscalyear, details_filter,
                                                        start, stop)

            partner_details_by_ids = self._get_account_partners_details(account_ids, details_filter, fiscalyear,
                                                                        target_move, start, stop,
                                                                        partner_filter_ids=partner_filter_ids)
            
            for account_id in account_ids:
                accounts_details_by_ids[account_id]['account'] = accounts_by_ids[account_id]
                accounts_details_by_ids[account_id]['partners_amounts'] = partner_details_by_ids[account_id]

            comp_params = {
                'comparison_filter': comparison_filter,
                'fiscalyear': fiscalyear,
                'start': start,
                'stop': stop,
                'initial_balance': init_balance,
            }

        return accounts_details_by_ids, comp_params

    def compute_partner_balance_data(self, data, filter_report_type=None):
        new_ids = data['form']['account_ids'] or data['form']['chart_account_id']
        max_comparison = self._get_form_param('max_comparison', data, default=0)
        main_filter = self._get_form_param('filter', data, default='filter_no')

        comp_filters, nb_comparisons, comparison_mode = self._comp_filters(data, max_comparison)

        fiscalyear = self.get_fiscalyear_br(data)

        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        init_bal = self.is_initial_balance_enabled(main_filter)
        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        chart_account = self._get_chart_account_id_br(data)
        result_selection = self._get_form_param('result_selection', data)
        partner_ids = self._get_form_param('partner_ids', data)

        filter_type = self._get_filter_type(result_selection)

        start_period, stop_period, start, stop = \
            self._get_start_stop_for_filter(main_filter, fiscalyear, start_date, stop_date, start_period, stop_period)

        # Retrieving accounts
        account_ids = self.get_all_accounts(new_ids, filter_view=False, filter_type=filter_type,
                                            filter_report_type=filter_report_type)

        # get details for each accounts, total of debit / credit / balance
        accounts_by_ids = self._get_account_details(account_ids, target_move, init_bal,
                                                    fiscalyear, main_filter, start, stop)

        partner_details_by_ids = self._get_account_partners_details(account_ids,
                                                                    main_filter,
                                                                    fiscalyear,
                                                                    target_move,
                                                                    start,
                                                                    stop,
                                                                    partner_filter_ids=partner_ids)

        comparison_params = []
        comp_accounts_by_ids = []
        for index in range(max_comparison):
            if comp_filters[index] != 'filter_no':
                comparison_result, comp_params = self._get_partners_comparison_details(data, account_ids, target_move, comp_filters[index], index)
                comparison_params.append(comp_params)
                comp_accounts_by_ids.append(comparison_result)
        objects = []

        for account_id in account_ids:
            if not accounts_by_ids[account_id]['parent_id']:  # hide top level account
                continue
            accounts = defaultdict(dict)
            accounts['current']['account'] = accounts_by_ids[account_id]
            accounts['current']['partners_amounts'] = partner_details_by_ids[account_id]
            comp_accounts = []
            for comp_account_by_id in comp_accounts_by_ids:
                values = comp_account_by_id.get(account_id)

                values['account'].update(self._get_diff(accounts['current']['account']['balance'], values.get('balance', 0.0)))
                comp_accounts.append(values)

                for partner_id, partner_values in values['partners_amounts'].copy().iteritems():
                    base_partner_balance = accounts['current']['partners_amounts']['partner_id']['balance'] if \
                                           accounts['current']['partners_amounts'].get('partner_id') else 0.0
                    partner_values.update(self._get_diff(base_partner_balance,
                                                         partner_values.get('balance', 0.0)))
                    values['partners_amounts'][partner_id].update(partner_values)

            accounts['comparisons'] = comp_accounts

            # TODO compute unallocated = difference between sum of partners and account  
            accounts['unallocated'] = {}

            all_partner_ids = reduce(add, [comp['partners_amounts'].keys() for comp in comp_accounts],
                                     accounts['current']['partners_amounts'].keys())
            accounts['partners_order'] = self._order_partners(all_partner_ids)
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
