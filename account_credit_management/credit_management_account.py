# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2012 Camptocamp SA
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
from datetime import datetime

from openerp.osv.orm import Model, fields
from openerp.tools.translate import _

class AccountAccount(Model):
    """Add a link to a credit management profile on account account"""


    def _check_account_type_compatibility(self, cursor, uid, acc_ids, context=None):
        """We check that account is of type reconcile"""
        if not isinstance(acc_ids, list):
            acc_ids = [acc_ids]
        for acc in self.browse(cursor, uid, acc_ids, context):
            if acc.credit_profile_id and not acc.reconcile:
                return False
        return True

    _inherit = "account.account"
    _description = """Add a link to a credit profile"""
    _columns = {'credit_profile_id': fields.many2one('credit.management.profile',
                                                     'Credit management profile',
                                                     help=("Define global credit profile"
                                                           "order is account partner invoice"))}

    _constraints = [(_check_account_type_compatibility,
                     _('You can not set a credit profile on a non reconciliable account'),
                     ['credit_profile_id'])]

class AccountInvoice(Model):
    """Add a link to a credit management profile on account account"""

    _inherit = "account.invoice"
    _description = """Add a link to a credit profile"""
    _columns = {'credit_profile_id': fields.many2one('credit.management.profile',
                                                     'Credit management profile',
                                                     help=("Define global credit profile"
                                                           "order is account partner invoice"))}
    def action_move_create(self, cursor, uid, ids, context=None):
        """We ensure writing of invoice id in move line because
           Trigger field may not work without account_voucher"""
        res = super(AccountInvoice, self).action_move_create(cursor, uid, ids, context=context)
        for inv in self.browse(cursor, uid, ids, context=context):
            if inv.move_id:
                for line in inv.move_id.line_id:
                    line.write({'invoice_id': inv.id})
        return res


class AccountMoveLine(Model):
    """Add a function field tha link the invoice to the move line
       It is mostly a performance trick as function search is way too
       ineffective. It adds a function field to store invoice id we do not modify the
       exisitng invoice string in order not to introduce regression.
       If we merge into core we need to write the existing invoice field"""

    _inherit = "account.move.line"
    # Stor fields has strange behavior with voucher module
    # def _invoice_id(self, cursor, user, ids, name, arg, context=None):
    #     #Code taken from OpenERP account addon
    #     invoice_obj = self.pool.get('account.invoice')
    #     res = {}
    #     for line_id in ids:
    #         res[line_id] = False
    #     cursor.execute('SELECT l.id, i.id ' \
    #                     'FROM account_move_line l, account_invoice i ' \
    #                     'WHERE l.move_id = i.move_id ' \
    #                     'AND l.id IN %s',
    #                     (tuple(ids),))
    #     invoice_ids = []
    #     for line_id, invoice_id in cursor.fetchall():
    #         res[line_id] = invoice_id
    #         invoice_ids.append(invoice_id)
    #     invoice_names = {False: ''}
    #     for invoice_id, name in invoice_obj.name_get(cursor, user, invoice_ids, context=context):
    #         invoice_names[invoice_id] = name
    #     for line_id in res.keys():
    #         invoice_id = res[line_id]
    #         res[line_id] = (invoice_id, invoice_names[invoice_id])
    #     return res

    # def _get_invoice(self, cursor, uid, ids, context=None):
    #     result = set()
    #     for line in self.pool.get('account.invoice').browse(cursor, uid, ids, context=context):
    #         if line.move_id:
    #             ids = [x.id for x in line.move_id.line_id or []]
    #     return list(result)

    # _columns = {'invoice_id': fields.function(_invoice_id, string='Invoice',
    #             type='many2one', relation='account.invoice',
    #             store={'account.invoice': (_get_invoice, ['move_id'], 20)})}

    _columns = {'invoice_id': fields.many2one('account.invoice', 'Invoice')}


    def _compute_residual_currency(self, cursor, uid, mv_line_br, lookup_date):
        """Compute residual of a line with currency"""
        cur_obj = self.pool.get('res.currency')
        move_line_total = 0.0
        for payment_line in mv_line_br.reconcile_partial_id.line_partial_ids:
            if self._should_exlude_line(mv_line_br, lookup_date):
                continue
            if (payment_line.currency_id and mv_line_br.currency_id
                and payment_line.currency_id.id == mv_line_br.currency_id.id):
                move_line_total += payment_line.amount_currency
            else:
                context_unreconciled = ({'date': payment_line.date})
                amount_in_foreign_currency = cur_obj.compute(cursor,
                                                             uid,
                                                             mv_line_br.company_id.currency_id.id,
                                                             mv_line_br.currency_id.id,
                                                             (payment_line.debit - payment_line.credit),
                                                             round=False,
                                                             context=context_unreconciled)
                move_line_total += amount_in_foreign_currency
        return move_line_total


    def _compute_residual_standard(self, cursor, uid, mv_line_br, lookup_date):
        """Compute residual of a line without currency"""
        move_line_total = 0.0
        for payment_line in mv_line_br.reconcile_partial_id.line_partial_ids:
            if self._should_exlude_line(mv_line_br, lookup_date):
                continue
            move_line_total += (payment_line.debit - payment_line.credit)
        return move_line_total


    def _should_exlude_line(self, mv_line_br, payment_line, lookup_date):
        """Check if line is applicable"""
        if payment_line.id == mv_line_br.id:
            return True
        if (datetime.strptime(payment_line.date, "%Y-%m-%d").date()
            > datetime.strptime(lookup_date, "%Y-%m-%d").date()):
            return True
        return False

    #TODO REWRITE function to take care of multiple payment that's gonna be fun
    def _amount_residual_from_date(self, cursor, uid, mv_line_br, lookup_date, context=None):
        """
        Code  taken from function _amount_residual of account/account_move_line.py
        TODO refactor it (gasp) once I have got time and be more advances in scenarios.
        Code computes residual amount at lookup date for mv_line_br in entry
        """
        context = context or {}
        if mv_line_br.reconcile_id:
            return (mv_line_br.amount_currency
                    or (mv_line_br.debit - mv_line_br.credit))
        if not mv_line_br.account_id.type in ('payable', 'receivable'):
            return (mv_line_br.amount_currency
                    or (mv_line_br.debit - mv_line_br.credit))
        if mv_line_br.reconcile_partial_id:
            if mv_line_br.currency_id:
                return self._compute_residual_currency(cursor, uid, mv_line_br, lookup_date)
            else:
                return self._compute_residual_standard(cursor, uid, mv_line_br, lookup_date)
