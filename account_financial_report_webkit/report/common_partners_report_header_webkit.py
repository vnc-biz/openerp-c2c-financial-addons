# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
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
#TODO split file
from common_report_header_webkit import CommonReportHeaderWebkit
from tools.translate import _

class CommonPartnersReportHeaderWebkit(CommonReportHeaderWebkit):
    """Define common helper for financial report"""
    
     ####################Initial Partner Balance helper ########################
    def _compute_partners_inital_balances(self, account_ids, start_period, fiscalyear, filter, partner_filter=None):
        """We compute initial balance.
        If form is filtered by date all initial balance are equal to 0
        This function will sum pear and apple in currency amount if account as no secondary currency"""
        final_res = {}
        period_ids = self._get_period_range_form_start_period(start_period, fiscalyear=False,
                                                                       include_special=False)
        if not period_ids:
            period_ids = [-1]
        # if opening period is included in start period we do not need to compute init balance
        # we just read it from opening entries
        res = {}
        if filter in ('filter_period', 'filter_no'):
            search_param = [start_period.date_start, tuple(period_ids), tuple(account_ids)]
            sql = ("SELECT account_id, partner_id,"
                   "     sum(debit-credit) as init_balance,"
                   "     sum(amount_currency) as init_balance_currency"
                   "   FROM account_move_line "
                   "   WHERE ((reconcile_id IS NULL)"
                   "           OR (reconcile_id IS NOT NULL AND last_rec_date > date(%s)))"
                   "     AND period_id in %s"
                   "     AND account_id in %s")
            if partner_filter:
                search_param.append(tuple(partner_filter))
                sql += "   AND partner_id in %s"
            sql += " group by account_id, partner_id"
            self.cursor.execute(sql, tuple(search_param))
            res = self.cursor.dictfetchall()
            import pprint; pprint.pprint(res)
            print '---------------------'
            if res:
                for row in res:
                    if not final_res.get(row['account_id']):
                        final_res[row['account_id']] = {}
                    final_res[row['account_id']][row['partner_id']] = \
                       {'init_balance': row['init_balance'], 
                        'init_balance_currency': row['init_balance_currency'] }
        if not final_res:
            for acc_id in account_ids:
                final_res[acc_id] = {}
        return final_res
     
     
    ####################Partner specific helper ################################    
    def get_patner_ids_from_account_move_lines(self, line_ids):
       """We get the partner linked to all current accounts that are used.
          We also use ensure that partner are ordered bay name"""
       base_dict = {}
       if not isinstance(account_ids, list):
           account_ids = [account_ids]
       sql = ("SELECT DISTINCT partner_id from account_move_line where account_id in %S"
              " AND partner_id IS NOT NULL")
       self.cursor.execute(sql, (tuple(account_ids),))
       res = cr.fetchall()
       if not res:
           return base_dict
       for acc_ids in account_ids:
           base_dict
