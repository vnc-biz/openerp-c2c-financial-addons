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
                account.update(init_balance[account['id']])
                account['balance'] = account['init_balance'] + account['debit'] - account['credit']
            accounts_by_id[account['id']] = account

        return accounts_by_id
