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

def sign(number):
    return cmp(number, 0)

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
            'report_name': _('Trial Balance'),
            'display_account': self._get_display_account,
            'display_account_raw': self._get_display_account_raw,
            'filter_form': self._get_filter,
            'target_move': self._get_target_move,
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

    def set_context(self, objects, data, ids, report_type=None):
        """Populate a ledger_lines attribute on each browse record that will be used
        by mako template"""
        new_ids = data['form']['account_ids'] or data['form']['chart_account_id']

        # Reading form
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

        init_bal = False
        if main_filter in ('filter_no', 'filter_period') \
            and comparison_mode == 'no_comparison' and fiscalyear:
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

        self.localcontext.update({
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
        })

        return super(TrialBalanceWebkit, self).set_context(objects, data, new_ids,
                                                            report_type=report_type)

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

HeaderFooterTextWebKitParser('report.account.account_report_trial_balance_webkit',
                             'account.account',
                             'addons/account_financial_report_webkit/report/templates/account_report_trial_balance.mako',
                             parser=TrialBalanceWebkit)
