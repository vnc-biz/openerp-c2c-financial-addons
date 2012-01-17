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
        'amount_currency': fields.boolean("With Currency",
                                          help="It adds the currency column"),
        'partner_ids': fields.many2many('res.partner', 'wiz_part_rel',
                                        'partner_id', 'wiz_id', 'Filter on partner',
                                         help="Only selected partners will be printed. Leave empty to print all partners."),
        'filter': fields.selection([('filter_no', 'No Filters'),
                                    ('filter_date', 'Date'),
                                    ('filter_period', 'Periods')], "Filter by", required=True, help='Filter by date : no opening balance will be displayed. (opening balance can only be calculated based on period to be correct).'),
    }
    _defaults = {
        'amount_currency': False,
        'exclude_reconciled': lambda self, cr, uid, context: context.get('open_transactions_report', False),
        'result_selection': 'customer_supplier',
    }

    def _check_fiscalyear(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], ['fiscalyear_id', 'filter'], context=context)
        if not obj['fiscalyear_id'] and obj['filter'] == 'filter_no':
            return False
        return True

    _constraints = [
        (_check_fiscalyear, 'When no Fiscal year is selected, you must choose to filter by periods or by date.', ['filter']),
    ]

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(AccountReportPartnersLedgerWizard, self).pre_print_report(cr, uid, ids, data, context)
        if context is None:
            context = {}
        vals = self.read(cr, uid, ids,
                         ['amount_currency', 'partner_ids',],
                         context=context)[0]
        data['form'].update(vals)
        return data

    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}
        # we update form with display account value
        data = self.pre_print_report(cursor, uid, ids, data, context=context)
        # GTK client problem onchange does not consider in save record
        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_partners_ledger_webkit',
                'datas': data}

AccountReportPartnersLedgerWizard()
