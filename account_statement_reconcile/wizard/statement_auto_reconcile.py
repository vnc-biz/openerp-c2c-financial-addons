# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Guewen Baconnier
#    Copyright 2011-2012 Camptocamp SA
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

import netsvc

from osv import osv, fields
from tools.translate import _
from operator import itemgetter
from itertools import groupby

logger = netsvc.Logger()


class AccountsStatementAutoReconcile(osv.osv_memory):
    _name = 'account.statement.import.automatic.reconcile'
    _description = 'Automatic Reconcile'

    _columns = {
        'account_ids': fields.many2many('account.account',
                                        'statement_reconcile_account_rel',
                                        'reconcile_id',
                                        'account_id',
                                        'Accounts to Reconcile',
                                        domain=[('reconcile', '=', True)]),
        'partner_ids': fields.many2many('res.partner',
                                        'statement_reconcile_res_partner_rel',
                                        'reconcile_id',
                                        'res_partner_id',
                                        'Partners to Reconcile'),
        'invoice_ids': fields.many2many('account.invoice',
                                        'statement_account_invoice_rel',
                                        'reconcile_id',
                                        'invoice_id',
                                        'Invoices to Reconcile',
                                        domain = [('type','=','out_invoice')]),
        'writeoff_acc_id': fields.many2one('account.account', 'Account'),
        'writeoff_amount_limit': fields.float('Max amount allowed for write off'),
        'journal_id': fields.many2one('account.journal', 'Journal'),
        'period_id': fields.many2one('account.period', 'Period'),
        'reconciled': fields.integer('Reconciled transactions', readonly=True),
        'allow_write_off': fields.boolean('Allow write off'),
    }

    def _get_reconciled(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('reconciled', 0)

    _defaults = {
        'reconciled': _get_reconciled,
    }

    def return_stats(self, cr, uid, reconciled, context=None):
        obj_model = self.pool.get('ir.model.data')
        context = context or {}
        context.update({'reconciled': reconciled})
        model_data_ids = obj_model.search(
            cr, uid,
            [('model','=','ir.ui.view'),
             ('name','=','stat_account_automatic_reconcile_view1')]
        )
        resource_id = obj_model.read(
            cr, uid, model_data_ids, fields=['res_id'])[0]['res_id']
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.statement.import.automatic.reconcile',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': context,
        }

    def _below_write_off_limit(self, cr, uid, lines,
                               writeoff_limit, context=None):

        keys = ('debit', 'credit')
        sums = reduce(lambda x, y:
                      dict((k, v + y[k]) for k, v in x.iteritems() if k in keys),
                      lines)
        debit, credit = sums['debit'], sums['credit']
        writeoff_amount = debit - credit
        return bool(writeoff_limit >= abs(writeoff_amount))

    def _query_moves(self, cr, uid, form, context=None):
        account_ids = [str(x.id) for x in form.account_ids]
        sql_params = {'account_ids': tuple(account_ids)}
        sql = ("SELECT l.account_id, i.transaction_id, i.origin, "
               "i.id AS invoice_id, m.id AS move_id, l.id AS move_line_id, "
               "l.debit, l.credit "
               "FROM account_invoice i "
               "LEFT JOIN account_move m "
               "ON m.id = i.move_id "
               "RIGHT JOIN account_move_line l "
               "ON l.move_id = m.id "
               "WHERE (i.reconciled = 'f' OR i.reconciled IS NULL) "
               "AND i.type ='out_invoice' "
               "AND (i.transaction_id IS NOT NULL or i.origin IS NOT NULL) "
               "AND i.move_id is NOT NULL "
               "AND l.reconcile_id IS NULL "
               "AND l.state = 'valid' "
               "AND l.account_id IN %(account_ids)s ")
        if form.invoice_ids:
            invoice_ids = [str(x.id) for x in form.invoice_ids]
            sql += "AND i.id IN %(invoice_ids)s "
            sql_params['invoice_ids'] = tuple(invoice_ids)
        if form.partner_ids:
            partner_ids = [str(x.id) for x in form.partner_ids]
            sql += "AND i.partner_id IN %(partner_ids)s "
            sql_params['partner_ids'] = tuple(partner_ids)
        cr.execute(sql, sql_params)
        return cr.dictfetchall()

    def _query_payments(self, cr, uid, account_id, invoice_move_ids, context=None):
        sql_params = {'account_id': account_id,
                      'invoice_move_ids': tuple(invoice_move_ids)}
        sql = ("SELECT l.id, l.move_id, "
               "l.ref, l.name, "
               "l.debit, l.credit "
               "FROM account_move_line l "
               "INNER JOIN account_move m "
               "ON m.id = l.move_id "
               "WHERE l.account_id = %(account_id)s "
               "AND l.move_id NOT IN %(invoice_move_ids)s "
               "AND l.reconcile_id IS NULL "
               "AND NOT EXISTS (select id FROM account_invoice i WHERE i.move_id = m.id) "
               "AND l.credit > 0")

        cr.execute(sql, sql_params)
        return cr.dictfetchall()

    @staticmethod
    def _groupby_keys(keys, lines):
        res = {}
        key = keys.pop(0)
        sorted_lines = sorted(lines, key=itemgetter(key))

        for reference, iter_lines in groupby(sorted_lines, itemgetter(key)):
            group_lines = list(iter_lines)

            if keys:
                group_lines = (AccountsStatementAutoReconcile.
                    _groupby_keys(keys[:], group_lines))
            else:
                # as we sort on all the keys, the last list
                # is perforce alone in the list
                group_lines = group_lines[0]
            res[reference] = group_lines

        return res

    def _search_payment_ref(self, cr, uid, all_payments,
                            reference_key, reference, context=None):
        def compare_key(payment, key, reference_patterns):
            if not payment.get(key):
                return False
            if payment.get(key).lower() in reference_patterns:
                return True

        res = []
        if not reference:
            return res

        lref = reference.lower()
        reference_patterns = (lref, 'tid_' + lref, 'tid_mag_' + lref)
        res_append = res.append
        for payment in all_payments:
            if (compare_key(payment, 'ref', reference_patterns) or
               compare_key(payment, 'name', reference_patterns)):
                res_append(payment)
                # remove payment from all_payments?

#        if res:
#            print '----------------------------------'
#            print 'ref: ' + reference
#            for l in res:
#                print (l.get('ref','') or '') + '    ' + (l.get('name','') or '')
        return res

    def _search_payments(self, cr, uid, all_payments,
                         references, context=None):
        payments = []
        for field_reference in references:
            ref_key, reference = field_reference
            payments = self._search_payment_ref(
                cr, uid, all_payments, ref_key, reference, context=context)
            # if match is found for one reference (transaction_id or origin)
            # we have found our payments, don't need to search for the order
            # reference
            if payments:
                break
        return payments

    def reconcile(self, cr, uid, form_id, context=None):
        context = context or {}
        move_line_obj = self.pool.get('account.move.line')

        if isinstance(form_id, list):
            form_id = form_id[0]

        form = self.browse(cr, uid, form_id)

        allow_write_off = form.allow_write_off

        if not form.account_ids :
            raise osv.except_osv(_('UserError'),
                                 _('You must select accounts to reconcile'))

        # returns a list with a dict per line :
        # [{'reference': 'A', 'invoice_id': 1, 'move_id': 1, 'move_line_id': 1},
        #  {'reference': 'A', 'invoice_id': 1, 'move_id': 1, 'move_line_id': 2},
        #  {'reference': 'B', 'invoice_id': 3, 'move_id': 3, 'move_line_id': 3}],
        moves = self._query_moves(cr, uid, form, context=context)
        if not moves:
            return False
        # returns a tree :
        # {'A': {1: {1: {1: {'reference': 'A', 'invoice_id': 1, 'move_id': 1, 'move_line_id': 1}},
        #               {2: {'reference': 'A', 'invoice_id': 1, 'move_id': 2, 'move_line_id': 2}}}},
        #  'B': {3: {3: {3: {'reference': 'B', 'invoice_id': 3, 'move_id': 3, 'move_line_id': 3}}}}}
        moves_tree = self._groupby_keys(['account_id',
                                         'invoice_id',
                                         'move_id',
                                         'move_line_id'],
                                         moves)

        reconciled = 0
        ### Set the date for reconcile
        if not context.has_key('date_p') or (context.has_key('date_p') and not context['date_p']):
            # TODO check date to set
            context['date_p'] = form.period_id.date_stop or False
            print str(context) 
        ###
        for account_id, account_tree in moves_tree.iteritems():
            # [0] because one move id per invoice
            account_move_ids = [invoice_tree.keys()[0] for
                                invoice_tree in account_tree.values()]

            account_payments = self._query_payments(cr, uid,
                                                    account_id,
                                                    account_move_ids,
                                                    context=context)

            for invoice_id, invoice_tree in account_tree.iteritems():

                # in any case one invoice = one move
                move_id, move_tree = invoice_tree.items()[0]

                move_line_ids = []
                move_lines = []
                move_lines_ids_append = move_line_ids.append
                move_lines_append = move_lines.append
                for move_line_id, vals in move_tree.iteritems():
                    move_lines_ids_append(move_line_id)
                    move_lines_append(vals)

                # take the first one because the reference
                # is the same everywhere for an invoice
                transaction_id = move_lines[0]['transaction_id']
                origin = move_lines[0]['origin']

                references = (('transaction_id', transaction_id),
                              ('origin', origin))

                payments = self._search_payments(
                    cr, uid, account_payments, references, context=context)

                if not payments:
                    continue

                payment_ids = [p['id'] for p in payments]

                reconcile_ids = move_line_ids + payment_ids
                do_write_off = (allow_write_off and
                                self._below_write_off_limit(
                                     cr, uid, move_lines + payments,
                                     form.writeoff_amount_limit,
                                     context=context))
                try:
                    if do_write_off:
                        move_line_obj.reconcile(cr,
                                                uid,
                                                reconcile_ids,
                                                'auto',
                                                form.writeoff_acc_id.id,
                                                form.period_id.id,
                                                form.journal_id.id,
                                                context)
                        logger.notifyChannel("Auto statement reconcile", netsvc.LOG_INFO,
                            _("Reconciled with write-off invoice id %s") % (invoice_id,))
                    else:
                        move_line_obj.reconcile_partial(cr,
                                                        uid,
                                                        reconcile_ids,
                                                        'manual',
                                                        context=context)
                        logger.notifyChannel("Auto statement reconcile", netsvc.LOG_INFO,
                            _("Reconciled invoice id %s") % (invoice_id,))
                except Exception, exc:
                    logger.notifyChannel("Auto statement reconcile", netsvc.LOG_ERROR,
                        _("Can't reconcile invoice id %s because: %s") % (invoice_id, exc,))
                reconciled += 1
                cr.commit()
        return self.return_stats(cr, uid, reconciled, context)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
