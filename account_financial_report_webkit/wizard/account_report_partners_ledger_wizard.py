# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
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
from osv import fields, osv


class AccountReportPartnersLedgerWizard(osv.osv_memory):
    """Will launch partner ledger report and pass required args"""

    _inherit = "account.common.partner.report"
    _name = "account.report.partners.ledger.webkit"
    _description = "Partner Ledger Report"

    _columns = {
        'initial_balance': fields.boolean("Include initial balances",
                                          help='It adds initial balance row'),
        'amount_currency': fields.boolean("With Currency",
                                          help="It adds the currency column"),
        'exclude_reconciled': fields.boolean("Exclude reconciled entries",),
        'until_date': fields.date("Clearance date",
                                  required=True,
                                  help="""The clearance date is essentially a tool used for debtors provisionning calculation.
                                        
By default, this date is equal to the the end date (ie: 31/12/2011 if you select fy 2011).

By amending the clearance date, you will be, for instance, able to answer the question : 'based on my last year end debtors open invoices, which invoices are still unpaid today (today is my clearance date)?'
"""),
        'partner_ids': fields.many2many('res.partner', 'wiz_part_rel',
                                        'partner_id', 'wiz_id', 'Filter on partner',
                                         help="Only selected partners will be printed. Leave empty to print all partners."),
        'filter': fields.selection([('filter_no', 'No Filters'),
                                    ('filter_date', 'Date'),
                                    ('filter_period', 'Periods')], "Filter by", required=True, help='Filter by date : no opening balance will be displayed. (opening balance can only be calculated based on period to be correct).'),

    }
    _defaults = {
        'amount_currency': False,
        'initial_balance': True,
        'exclude_reconciled': True,
        'result_selection': 'customer_supplier',
    }

    def _check_until_date(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], ['fiscalyear_id', 'period_to', 'date_to', 'until_date'], context=context)
        min_date = self.default_until_date(cr, uid, ids, obj['fiscalyear_id'], obj['period_to'], obj['date_to'], context=context)
        if min_date and obj['until_date'] < min_date:
            return False
        return True

    def _check_fiscalyear(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], ['fiscalyear_id', 'filter'], context=context)
        if not obj['fiscalyear_id'] and obj['filter'] == 'filter_no':
            return False
        return True

    _constraints = [
        (_check_until_date, 'Clearance date is too early.', ['until_date']),
        (_check_fiscalyear, 'When no Fiscal year is selected, you must choose to filter by periods or by date.', ['filter']),
    ]

    def default_until_date(self, cursor, uid, ids, fiscalyear_id=False, period_id=False, date_to=False, context=None):
        res_date = False
        # first priority: period or date filters
        if period_id:
            res_date = self.pool.get('account.period').read(cursor, uid, period_id, ['date_stop'], context=context)['date_stop']
        elif date_to:
            res_date = date_to
        elif fiscalyear_id:
            res_date = self.pool.get('account.fiscalyear').read(cursor, uid, fiscalyear_id, ['date_stop'], context=context)['date_stop']

        return res_date

    def onchange_fiscalyear(self, cursor, uid, ids, fiscalyear=False, period_id=False, date_to=False, until_date=False, context=None):
        res = {'value': {}}
        if not fiscalyear:
            res['value']['initial_balance'] = False
        res['value']['until_date'] = self.default_until_date(cursor, uid, ids,
                                                             fiscalyear_id=fiscalyear,
                                                             period_id=period_id,
                                                             date_to=date_to,
                                                             context=context)
        return res

    def onchange_date_to(self, cursor, uid, ids, fiscalyear=False, period_id=False, date_to=False, until_date=False, context=None):
        res = {'value': {}}
        res['value']['until_date'] = self.default_until_date(cursor, uid, ids,
                                                             fiscalyear_id=fiscalyear,
                                                             period_id=period_id,
                                                             date_to=date_to,
                                                             context=context)
        return res

    def onchange_period_to(self, cursor, uid, ids, fiscalyear=False, period_id=False, date_to=False, until_date=False, context=None):
        res = {'value': {}}
        res['value']['until_date'] = self.default_until_date(cursor, uid, ids,
                                                             fiscalyear_id=fiscalyear,
                                                             period_id=period_id,
                                                             date_to=date_to,
                                                             context=context)
        return res

    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = super(AccountReportPartnersLedgerWizard, self).onchange_filter(cr, uid, ids, filter=filter, fiscalyear_id=fiscalyear_id, context=context)
        if res.get('value', False):
            res['value']['until_date'] = self.default_until_date(cr, uid, ids,
                                                                 fiscalyear_id=fiscalyear_id,
                                                                 period_id=res['value'].get('period_to', False),
                                                                 date_to=res['value'].get('date_to', False),
                                                                 context=context)
        return res


    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(AccountReportPartnersLedgerWizard, self).pre_print_report(cr, uid, ids, data, context)
        if context is None:
            context = {}
        vals = self.read(cr, uid, ids,
                         ['initial_balance', 'amount_currency', 'partner_ids',
                          'until_date', 'exclude_reconciled'],
                         context=context)[0]
        data['form'].update(vals)
        return data

    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}
        # we update form with display account value
        data = self.pre_print_report(cursor, uid, ids, data, context=context)
        # GTK client problem onchange does not consider in save record
        if not data['form']['fiscalyear_id'] or data['form']['filter'] == 'filter_date':
            data['form'].update({'initial_balance': False})
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_partners_ledger_webkit',
                'datas': data}

AccountReportPartnersLedgerWizard()
