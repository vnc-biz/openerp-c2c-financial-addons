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
from osv import fields, osv


class AccountReportPartnersLedgerWizard(osv.osv_memory):
    """Will launch partner ledger report and pass requiered args"""


    _inherit = "account.common.account.report"
    _name = "account.report.partners.ledger.webkit"
    _description = "Partner Ledger Report"

    _columns = {
        'initial_balance': fields.boolean("Include initial balances",
                                          help='It adds initial balance row'),

        'amount_currency': fields.boolean("With Currency",
                                          help="It adds the currency column"),

        'display_account': fields.selection([('bal_all', 'All'),
                                             ('bal_mix', 'With transactions or non zero balance')],
                                            'Display accounts',
                                            required=True),
        'include_reconciled': fields.boolean("Include reconciled entries",
                                help="TODO"),
        'include_reconciled_date': fields.date("Reconciled entries date",
                                help="TODO"),
        'partner_ids': fields.many2many('res.partner', 'wiz_part_rel', 
                                        'partner_id', 'wiz_id','Filter on partner',
                                         help="TODO"),
        'account_type': fields.selection([('all', 'Payable and Receivable'),
                                          ('pay', 'Payable only'),
                                          ('rec', 'Receivable only')],
                                         'Filter on account type',
                                         help="TODO"),
    }
    _defaults = {
        'amount_currency': False,
        'initial_balance': False,
    }

    def onchange_fiscalyear(self, cursor, uid, ids, fiscalyear=False, context=None):
        res = {}
        if not fiscalyear:
            res['value'] = {'initial_balance': False}
        return res

    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}
        # we update form with display account value
        data = self.pre_print_report(cursor, uid, ids, data, context=context)
        vals = self.read(cursor, uid, ids, ['initial_balance', 'amount_currency'])[0]

        data['form'].update(vals)
        # GTK client problem onchange does not consider in save record
        if not data['form']['fiscalyear_id']:
            data['form'].update({'initial_balance': False})
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.TOSET',
                'datas': data}

AccountReportPartnersLedgerWizard()
