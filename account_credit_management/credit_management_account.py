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
from openerp.osv.orm import Model, fields

class AccountAccount(Model):
    """Add a link to a credit management profile on account account"""

    _inherit = "account.account"
    _description = """Add a link to a credit profile"""
    _columns = {'credit_profile_id': fields.many2one('credit.management.profile',
                                                     'Credit management profile',
                                                     help=("Define global credit profile"
                                                           "order is account partner invoice"))}

class AccountInvoice(Model):
    """Add a link to a credit management profile on account account"""

    _inherit = "account.invoice"
    _description = """Add a link to a credit profile"""
    _columns = {'credit_profile_id': fields.many2one('credit.management.profile',
                                                     'Credit management profile',
                                                     help=("Define global credit profile"
                                                           "order is account partner invoice"))}


class AccountMoveLine(Model):
    """Add a function field tha link the invoice to the move line
       It is mostly a performance trick as function search is way too
       ineffective. It adds a function field to store invoice id we do not modify the
       exisitng invoice string in order not to introduce regression.
       If we merge into core we need to write the existing invoice field"""

    _inherit = "account.move.line"

    def _invoice_id(self, cursor, user, ids, name, arg, context=None):
        #Code taken from OpenERP account addon
        invoice_obj = self.pool.get('account.invoice')
        res = {}
        for line_id in ids:
            res[line_id] = False
        cursor.execute('SELECT l.id, i.id ' \
                        'FROM account_move_line l, account_invoice i ' \
                        'WHERE l.move_id = i.move_id ' \
                        'AND l.id IN %s',
                        (tuple(ids),))
        invoice_ids = []
        for line_id, invoice_id in cursor.fetchall():
            res[line_id] = invoice_id
            invoice_ids.append(invoice_id)
        invoice_names = {False: ''}
        for invoice_id, name in invoice_obj.name_get(cursor, user, invoice_ids, context=context):
            invoice_names[invoice_id] = name
        for line_id in res.keys():
            invoice_id = res[line_id]
            res[line_id] = (invoice_id, invoice_names[invoice_id])
        return res

    _columns = {'invoice_id': fields.function(_invoice_id, string='Invoice',
                type='many2one', relation='account.invoice', store=True)}
