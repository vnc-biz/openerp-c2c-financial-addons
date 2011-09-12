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
import pooler

from collections import defaultdict
from operator import add
from report import report_sxw
from osv import osv
from tools.translate import _
from datetime import datetime

from common_partners_report_header_webkit import CommonPartnersReportHeaderWebkit
from webkit_parser_header_fix import HeaderFooterTextWebKitParser


class PartnersLedgerWebkit(report_sxw.rml_parse, CommonPartnersReportHeaderWebkit):

    def __init__(self, cursor, uid, name, context):
        super(PartnersLedgerWebkit, self).__init__(cursor, uid, name, context=context)
        self.pool = pooler.get_pool(self.cr.dbname)
        self.cursor = self.cr

        company = self.pool.get('res.users').browse(self.cr, uid, uid, context=context).company_id
        header_report_name = ' - '.join((_('PARTNER LEDGER'), company.name, company.currency_id.name))

        footer_date_time = self.formatLang(str(datetime.today()), date_time=True)

        self.localcontext.update({
            'cr': cursor,
            'uid': uid,
            'report_name':_('Partner Ledger'),
            'display_account_raw': self._get_display_account_raw,
            'filter_form': self._get_filter,
            'target_move': self._get_target_move,
            'initial_balance': self._get_initial_balance,
            'amount_currency': self._get_amount_currency,
            'display_partner_account': self._get_display_partner_account,
            'display_target_move': self._get_display_target_move,
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
        new_ids = data['form']['chart_account_id']

        # We memoize ledger lines linked to account. Key is account id
        # values are array of lines
        ledger_lines_memoizer = {}

        # Account initial balance memoizer
        init_balance_memoizer = {}
        # account partner memoizer
        account_partner_rel_memoizer = {}
        # Reading form
        init_bal = self._get_form_param('initial_balance', data)
        main_filter = self._get_form_param('filter', data, default='filter_no')
        target_move = self._get_form_param('target_move', data, default='all')
        start_date = self._get_form_param('date_from', data)
        stop_date = self._get_form_param('date_to', data)
        start_period = self.get_start_period_br(data)
        stop_period = self.get_end_period_br(data)
        fiscalyear = self.get_fiscalyear_br(data)
        partner_ids = self._get_form_param('partner_ids', data)
        result_selection = self._get_form_param('result_selection', data)
        exclude_reconcile = self._get_form_param('exclude_reconciled', data)
        date_until = self._get_form_param('until_date', data)
        chart_account = self._get_chart_account_id_br(data)

        if main_filter == 'filter_no' and fiscalyear:
            start_period = self.get_first_fiscalyear_period(fiscalyear)
            stop_period = self.get_last_fiscalyear_period(fiscalyear)

        # Retrieving accounts
        filter_type = ('payable', 'receivable')
        if result_selection == 'customer':
            filter_type = ('receivable',)
        if result_selection == 'supplier':
            filter_type = ('payable',)

        accounts = self.get_all_accounts(new_ids, filter_view=True,
                                         filter_type=filter_type)

        if init_bal and main_filter in ('filter_no', 'filter_period'):
            init_balance_memoizer = self._compute_partners_initial_balances(accounts,
                                                                            start_period,
                                                                            fiscalyear,
                                                                            main_filter,
                                                                            partner_filter=partner_ids,
                                                                            exclude_reconcile=exclude_reconcile)
        # computation of ledeger lines
        if main_filter == 'filter_date':
            start = start_date
            stop = stop_date
        else:
            start = start_period
            stop = stop_period
        ledger_lines_memoizer = self._compute_partner_ledger_lines(accounts,
                                                                   main_filter,
                                                                   target_move,
                                                                   start,
                                                                   stop,
                                                                   date_until,
                                                                   exclude_reconcile=exclude_reconcile,
                                                                   partner_filter=partner_ids)
        objects = []
        for account in self.pool.get('account.account').browse(self.cursor, self.uid, accounts):
            account.ledger_lines = ledger_lines_memoizer.get(account.id, {})
            account.init_balance = init_balance_memoizer.get(account.id, {})
            ## we have to compute partner order based on inital balance
            ## and ledger line as we may have partner with init bal
            ## that are not in ledger line and vice versa
            ledg_lines_pids = ledger_lines_memoizer.get(account.id, {}).keys()
            if init_bal:
                init_bal_lines_pids = init_balance_memoizer.get(account.id, {}).keys()
                account.init_balance = init_balance_memoizer.get(account.id, {})
            else:
                account.init_balance = {}
                init_bal_lines_pids = []
            account.partners_order = self._order_partners(ledg_lines_pids, init_bal_lines_pids)
            account.ledger_lines = ledger_lines_memoizer.get(account.id, {})
            objects.append(account)

        self.localcontext.update({
            'fiscalyear': fiscalyear,
            'start_date': start_date,
            'stop_date': stop_date,
            'start_period': start_period,
            'stop_period': stop_period,
            'date_until': date_until,
            'partner_ids': partner_ids,
            'exclude_reconcile': exclude_reconcile,
            'chart_account': chart_account,
        })

        return super(PartnersLedgerWebkit, self).set_context(objects, data, new_ids,
                                                            report_type=report_type)

    def _compute_partner_ledger_lines(self, accounts_ids, main_filter, target_move, start,
                                      stop, date_until, exclude_reconcile=True, partner_filter=False):
        res = defaultdict(dict)
        valid_only = True
        if target_move == 'all':
            valid_only = False
        ## we check if until date and date stop have the same value
        if main_filter in ('filter_period', 'filter_no'):
            date_stop = stop.date_stop
            date_match = (date_stop == date_until)

        elif main_filter == 'filter_date':
            date_stop = stop
            date_match = (stop == date_until)

        else:
            raise osv.except_osv(_('Unsuported filter'),
                                 _('Filter has to be in filter date, period, or none'))

        for acc_id in accounts_ids:
            # We get the move line ids of the account depending of the
            # way the initial balance was created we include or not opening entries
            move_line_ids_dict = self.get_partners_move_lines_ids(acc_id,
                                                             main_filter,
                                                             start,
                                                             stop,
                                                             exclude_reconcile=exclude_reconcile,
                                                             valid_only=valid_only,
                                                             partner_filter=partner_filter)
            if not move_line_ids_dict:
                #not really useful as it is default dict
                res[acc_id] = {}
                continue
            for partner_id in move_line_ids_dict:
                m_line_ids = move_line_ids_dict.get(partner_id, [])
                if not date_match and m_line_ids:  # no initial balance when filtering by date
                    m_line_ids += self._get_clearance_move_line_ids(m_line_ids, date_stop, date_until)
                lines = self._get_move_line_datas(list(set(m_line_ids)))
                res[acc_id][partner_id] = lines
        return res


HeaderFooterTextWebKitParser('report.account.account_report_partners_ledger_webkit',
                             'account.account',
                             'addons/account_financial_report_webkit/report/templates/account_report_partners_ledger.mako',
                             parser=PartnersLedgerWebkit)
