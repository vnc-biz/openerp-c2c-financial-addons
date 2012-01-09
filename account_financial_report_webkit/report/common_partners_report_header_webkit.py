# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
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
# TODO refactor helper in order to act more like mixin
# By using properties we will have a more simple signature in fuctions

from collections import defaultdict

from common_report_header_webkit import CommonReportHeaderWebkit
from tools.translate import _


class CommonPartnersReportHeaderWebkit(CommonReportHeaderWebkit):
    """Define common helper for partner oriented financial report"""

    ####################Account move line retrieval helper ##########################
    def get_partners_move_lines_ids(self, account_id, main_filter, start, stop, target_move,
                                    exclude_reconcile=True, partner_filter=False):
        filter_from = False
        if main_filter in ('filter_period', 'filter_no'):
            filter_from = 'period'
        elif main_filter == 'filter_date':
            filter_from = 'date'
        if filter_from:
            return self._get_partners_move_ids(filter_from,
                                               account_id,
                                               start,
                                               stop,
                                               target_move,
                                               exclude_reconcile=exclude_reconcile,
                                               partner_filter=partner_filter)


    def _get_query_params_from_periods(self, period_start, period_stop, mode='exclude_opening'):
        # we do not want opening period so we exclude opening
        periods = self._get_period_range_from_periods(period_start, period_stop, mode)
        if not periods:
            return []

        search_params = {'period_ids': tuple(periods),
                         'date_stop': period_stop.date_stop}

        sql_conditions = "  AND account_move_line.period_id in %(period_ids)s"

        return sql_conditions, search_params

    def _get_query_params_from_dates(self, date_start, date_stop, **args):

        periods = self._get_opening_periods()
        if not periods:
            periods = (-1,)

        search_params = {'period_ids': tuple(periods),
                         'date_start': date_start,
                         'date_stop': date_stop}

        sql_conditions = "  AND account_move_line.period_id not in %(period_ids)s" \
                         "  AND account_move_line.date between date(%(date_start)s) and date((%(date_stop)s))"

        return sql_conditions, search_params

    def _get_partners_move_ids(self, filter_from, account_id, start, stop, target_move,
                   exclude_reconcile=True,partner_filter=False):

        final_res = defaultdict(list)

        sql_select = "SELECT account_move_line.id, account_move_line.partner_id FROM account_move_line"
        sql_joins = ''
        sql_where = " WHERE account_move_line.account_id = %(account_ids)s " \
                    " AND account_move_line.state = 'valid' "
        
        sql_conditions, search_params = getattr(self, '_get_query_params_from_'+filter_from+'s')(start, stop)

        sql_where += sql_conditions

        if exclude_reconcile:
            sql_where += ("  AND ((account_move_line.reconcile_id IS NULL)"
                         "   OR (account_move_line.reconcile_id IS NOT NULL AND account_move_line.last_rec_date > date(%(date_stop)s)))")

        if partner_filter:
            sql_where += "   AND account_move_line.partner_id in %(partner_ids)s"

        if target_move == 'posted':
            sql_joins += "INNER JOIN account_move ON account_move_line.move_id = account_move.id"
            sql_where += " AND account_move.state = %(target_move)s"
            search_params.update({'target_move': target_move,})

        search_params.update({
            'account_ids': account_id,
            'partner_ids': tuple(partner_filter),
        })

        sql = ' '.join((sql_select, sql_joins, sql_where))
        self.cursor.execute(sql, search_params)
        res = self.cursor.dictfetchall()
        if res:
            for row in res:
                final_res[row['partner_id']].append(row['id'])
        return final_res

    def _get_clearance_move_line_ids(self, move_line_ids, date_stop, date_until):
        if not move_line_ids:
            return []
        move_line_obj = self.pool.get('account.move.line')
        # we do not use orm in order to gain perfo
        # In this case I have to test the effective gain over an itteration
        # Actually ORM does not allows distinct behavior
        sql = "Select distinct reconcile_id from account_move_line where id in %s"
        self.cursor.execute(sql, (tuple(move_line_ids),))
        rec_ids = self.cursor.fetchall()
        if rec_ids:
            rec_ids = [x[0] for x in rec_ids]
            l_ids = move_line_obj.search(self.cursor,
                                         self.uid,
                                         [('reconcile_id', 'in', rec_ids),
                                          ('date', '>=', date_stop),
                                          ('date', '<=', date_until)])
            return l_ids
        else:
            return []

     ####################Initial Partner Balance helper ########################
    def _compute_partners_initial_balances(self, account_ids, start_period, fiscalyear, main_filter, partner_filter=None, exclude_reconcile=False, force_period_ids=False):
        """We compute initial balance.
        If form is filtered by date all initial balance are equal to 0
        This function will sum pear and apple in currency amount if account as no secondary currency"""
        if isinstance(account_ids, (int, long)):
            account_ids = [account_ids]
        final_res = defaultdict(dict)
        period_ids = force_period_ids \
                     if force_period_ids \
                     else self._get_period_range_from_start_period(start_period, fiscalyear=False, include_opening=False)
        
        if not period_ids:
            period_ids = [-1]
        # if opening period is included in start period we do not need to compute init balance
        # we just read it from opening entries
        res = defaultdict(dict)
        if main_filter in ('filter_period', 'filter_no'):
            search_param = {'date_start': start_period.date_start,
                            'period_ids': tuple(period_ids),
                            'account_ids': tuple(account_ids),}
            sql = ("SELECT account_id, partner_id,"
                   "       sum(debit) as debit, sum(credit) as credit,"
                   "       sum(debit-credit) as init_balance,"
                   "       CASE WHEN a.currency_id ISNULL THEN 0.0 ELSE sum(amount_currency) END as init_balance_currency, "
                   "       c.name as currency_name "
                   "FROM account_move_line "
                   "INNER JOIN account_account a "
                   "ON a.id = account_id "
                   "LEFT JOIN res_currency c "
                   "ON c.id = a.currency_id "
                   "WHERE period_id in %(period_ids)s"
                   "AND account_id in %(account_ids)s")
            if exclude_reconcile:
                sql += ("AND ((reconcile_id IS NULL)"
                       "OR (reconcile_id IS NOT NULL AND last_rec_date < date(%(date_start)s)))")
            if partner_filter:
                sql += "AND partner_id in %(partner_ids)s"
                search_param.update({'partner_ids': tuple(partner_filter)})
            sql += "GROUP BY account_id, partner_id, a.currency_id, c.name"
            self.cursor.execute(sql, search_param)
            res = self.cursor.dictfetchall()
            if res:
                for row in res:
                    final_res[row['account_id']][row['partner_id']] = \
                    dict((key, row[key]) for key in ('debit', 'credit', 'init_balance', 'init_balance_currency', 'currency_name'))
        if not final_res:
            for acc_id in account_ids:
                final_res[acc_id] = {}

        return final_res

    ####################Partner specific helper ################################
    def _order_partners(self, *args):
        """We get the partner linked to all current accounts that are used.
            We also use ensure that partner are ordered by name
            args must be list"""
        res = []
        partner_ids = []
        for arg in args:
            if arg:
                partner_ids += arg
        if not partner_ids:
            return []

        existing_partner_ids = [partner_id for partner_id in partner_ids if partner_id]
        if existing_partner_ids:
            # We may use orm here as the performance optimization is not that big
            sql = ("SELECT name|| ' ' ||CASE WHEN ref IS NOT NULL THEN '('||ref||')' ELSE '' END, id, ref, name"
                   "  FROM res_partner WHERE id IN %s ORDER BY name, ref")
            self.cursor.execute(sql, (tuple(set(existing_partner_ids)),))
            res = self.cursor.fetchall()

        # move lines without partners, set None for empty partner
        if not all(partner_ids):
            res.append((None, None, None, None))

        if not res:
            return []
        return res
