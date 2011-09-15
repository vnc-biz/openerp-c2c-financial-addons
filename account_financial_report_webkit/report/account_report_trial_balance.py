# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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


from report import report_sxw
from tools.translate import _
import pooler
from operator import add, itemgetter
from itertools import groupby
from datetime import datetime

from common_balance_report_header_webkit import CommonBalanceReportHeaderWebkit
from webkit_parser_header_fix import HeaderFooterTextWebKitParser


class TrialBalanceWebkit(report_sxw.rml_parse, CommonBalanceReportHeaderWebkit):

    def __init__(self, cursor, uid, name, context):
        super(TrialBalanceWebkit, self).__init__(cursor, uid, name, context=context)
        self.pool = pooler.get_pool(self.cr.dbname)
        self.cursor = self.cr
        
        company = self.pool.get('res.users').browse(self.cr, uid, uid, context=context).company_id
        header_report_name = ' - '.join((_('TRIAL BALANCE'), company.name, company.currency_id.name))

        footer_date_time = self.formatLang(str(datetime.today()), date_time=True)

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name': _('General Ledger'),
            'display_account': self._get_display_account,
            'display_account_raw': self._get_display_account_raw,
            'filter_form': self._get_filter,
            'target_move': self._get_target_move,
            'amount_currency': self._get_amount_currency,
            'display_target_move': self._get_display_target_move,
            'accounts': self._get_accounts_br,
            'additional_args': [
                ('--header-font-name', 'Helvetica'),
                ('--footer-font-name', 'Helvetica'),
                ('--header-font-size', '10'),
                ('--footer-font-size', '6'),
                ('--header-left', header_report_name),
                ('--header-spacing', '2'),
                ('--footer-left', footer_date_time),
                ('--footer-right', ' '.join((_('Page'), '[page]', _('of'), '[topage]'))),
                ('--footer-line',),
            ],
        })

    def _get_comparison_details(self, data, account_ids, target_move, comparison_filter, index):
        """

        @param data: data of the wizard form
        @param account_ids: ids of the accounts to get details
        @param comparison_filter: selected filter on the form for the comparison (filter_no, filter_year, filter_period, filter_date)
        @param index: index of the fields to get (ie. comp1_fiscalyear_id where 1 is the index)
        @return: dict of account details (key = account id)
        """
        comp_fiscalyear = self._get_info(data, "comp%s_fiscalyear_id" % (index,), 'account.fiscalyear')
        comp_start_period = self._get_info(data, "comp%s_period_from" % (index,), 'account.period')
        comp_stop_period = self._get_info(data, "comp%s_period_to" % (index,), 'account.period')
        comp_start_date = self._get_form_param("comp%s_date_from" % (index,), data)
        comp_stop_date = self._get_form_param("comp%s_date_to" % (index,), data)

        comp_accounts_by_ids = {}
        if comparison_filter != 'filter_no':
            details_filter = comparison_filter
            if comparison_filter == 'filter_year':
                comp_start = self.get_first_fiscalyear_period(comp_fiscalyear)
                comp_stop = self.get_last_fiscalyear_period(comp_fiscalyear)
                details_filter = 'filter_period'  # same behavior as filter periods
            elif comparison_filter == 'filter_date':
                comp_start = comp_start_date
                comp_stop = comp_stop_date
            else:
                comp_start = comp_start_period
                comp_stop = comp_stop_period

            comp_accounts_by_ids = self._get_account_details(account_ids, target_move, False,
                                                              comp_fiscalyear, details_filter,
                                                              comp_start, comp_stop)
        return comp_accounts_by_ids

    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each browse record that will be used
        by mako template"""
        new_ids = data['form']['account_ids'] or data['form']['chart_account_id']

        # Reading form
        main_filter = self._get_form_param('filter', data, default='filter_no')
        comp1_filter = self._get_form_param('comp1_filter', data, default='filter_no')
        comp2_filter = self._get_form_param('comp2_filter', data, default='filter_no')
        fiscalyear = self.get_fiscalyear_br(data)

        init_bal = False
        if main_filter in ('filter_no', 'filter_period') \
            and comp1_filter == 'filter_no' \
            and fiscalyear:
            init_bal = True
        
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
        account_ids = self.get_all_accounts(new_ids, filter_view=False)

        # computation of ledger lines
        if main_filter == 'filter_date':
            start = start_date
            stop = stop_date
        else:
            start = start_period
            stop = stop_period

        accounts_by_ids = self._get_account_details(account_ids, target_move, init_bal,
                                                    fiscalyear, main_filter, start, stop)

        comp1_accounts_by_ids = {}
        if comp1_filter != 'filter_no':
            comp1_accounts_by_ids = self._get_comparison_details(data, account_ids, target_move, comp1_filter, 1)

        comp2_accounts_by_ids = {}
        if comp2_filter != 'filter_no':
            comp2_accounts_by_ids = self._get_comparison_details(data, account_ids, target_move, comp1_filter, 2)

        objects = []
        for account_id in account_ids:
            if not accounts_by_ids[account_id]['parent_id']:  # hide top level account
                continue
            accounts = {}
            accounts['current'] = accounts_by_ids[account_id]
            if comp1_accounts_by_ids:
                accounts['comparison1'] = comp1_accounts_by_ids[account_id]
                accounts['comparison1'].update(self._get_diff(accounts['comparison1']['balance'], accounts['current']['balance']))

            if comp2_accounts_by_ids:
                accounts['comparison2'] = comp2_accounts_by_ids[account_id]
                accounts['comparison2'].update(self._get_diff(accounts['comparison2']['balance'], accounts['current']['balance']))

            objects.append(accounts)

        self.localcontext.update({
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'chart_account': chart_account,
            'comparison_mode': comp1_filter != 'filter_no',
            'initial_balance': init_bal,
        })

        return super(TrialBalanceWebkit, self).set_context(objects, data, new_ids,
                                                            report_type=report_type)

    def _get_diff(self, balance, last_balance):
        """
        @param balance: current balance
        @param last_balance: last balance
        @return: dict of form {'diff': difference, 'percent_diff': diff in percentage}
        """
        diff = last_balance - balance
        percent_diff = 0.0

        obj_precision = self.pool.get('decimal.precision')
        precision = obj_precision.precision_get(self.cr, self.uid, 'Account')
        if diff and balance:
            percent_diff = round(diff / balance * 100, precision)
        return {'diff': diff, 'percent_diff': percent_diff}

HeaderFooterTextWebKitParser('report.account.account_report_trial_balance_webkit',
                             'account.account',
                             'addons/account_financial_report_webkit/report/templates/account_report_trial_balance.mako',
                             parser=TrialBalanceWebkit)
