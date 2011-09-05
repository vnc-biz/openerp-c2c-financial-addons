# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

from osv import fields, osv
from tools.translate import _

class account_statement_from_invoice_lines(osv.osv_memory):
    """
    Generate Entries by Statement from Invoices
    """
    _name = "account.statement.from.invoice.lines"
    _description = "Entries by Statement from Invoices"
    _columns = {
        'line_ids': fields.many2many('account.move.line', 'account_move_line_relation', 'move_id', 'line_id', 'Invoices'),
    }

    def populate_statement(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        statement_id = context.get('statement_id', False)
        if not statement_id:
            return {'type': 'ir.actions.act_window_close'}
        data =  self.read(cr, uid, ids, context=context)[0]
        line_ids = data['line_ids']
        if not line_ids:
            return {'type': 'ir.actions.act_window_close'}

        line_obj = self.pool.get('account.move.line')
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        currency_obj = self.pool.get('res.currency')
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        line_date = time.strftime('%Y-%m-%d')
        statement = statement_obj.browse(cr, uid, statement_id, context=context)
        journal_id = statement.journal_id.id

        # for each selected move lines
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if line.journal_id.type == 'sale':
                type = 'customer'
            elif line.journal_id.type == 'purchase':
                type = 'supplier'
            else:
                type = 'general'
            st_line_id = statement_line_obj.create(cr, uid, {
                'name': line.name or '?',
                'amount': line.amount_currency or ((line.debit or 0.0 )- (line.credit or 0.0)),
                'type': type,
                'partner_id': line.partner_id.id,
                'account_id': line.account_id.id,
                'statement_id': statement_id,
                'ref': line.ref,
                'date': time.strftime('%Y-%m-%d'),
            }, context=context)

            statement_line_obj.create_voucher(cr, uid, [st_line_id], line.id, journal_id, context=context)

        return {'type': 'ir.actions.act_window_close'}

account_statement_from_invoice_lines()

class account_statement_from_invoice(osv.osv_memory):
    """
    Generate Entries by Statement from Invoices
    """
    _name = "account.statement.from.invoice"
    _description = "Entries by Statement from Invoices"
    _columns = {
        'date': fields.date('Date payment',required=True),
        'journal_ids': fields.many2many('account.journal', 'account_journal_relation', 'account_id', 'journal_id', 'Journal'),
        'line_ids': fields.many2many('account.move.line', 'account_move_line_relation', 'move_id', 'line_id', 'Invoices'),
    }
    _defaults = {
        'date': lambda *a: time.strftime('%Y-%m-%d'),
    }

    def search_invoices(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_obj = self.pool.get('account.move.line')
        statement_obj = self.pool.get('account.bank.statement')
        journal_obj = self.pool.get('account.journal')
        mod_obj = self.pool.get('ir.model.data')
        statement_id = 'statement_id' in context and context['statement_id']

        data =  self.read(cr, uid, ids, context=context)[0]
        statement = statement_obj.browse(cr, uid, statement_id, context=context)
        args_move_line = []
        repeated_move_line_ids = []
        # Creating a group that is unique for importing move lines(move lines, once imported into statement lines, should not appear again)
        for st_line in statement.line_ids:
            args_move_line = []
            args_move_line.append(('name', '=', st_line.name))
            args_move_line.append(('ref', '=', st_line.ref))
            if st_line.partner_id:
                args_move_line.append(('partner_id', '=', st_line.partner_id.id))
            args_move_line.append(('account_id', '=', st_line.account_id.id))

            move_line_id = line_obj.search(cr, uid, args_move_line, context=context)
            if move_line_id:
                repeated_move_line_ids += move_line_id

        journal_ids = data['journal_ids']
        if journal_ids == []:
            journal_ids = journal_obj.search(cr, uid, [('type', 'in', ('sale', 'cash', 'purchase'))], context=context)

        args = [
            ('reconcile_id', '=', False),
            ('journal_id', 'in', journal_ids),
            ('account_id.reconcile', '=', True)]

        if repeated_move_line_ids:
            args.append(('id', 'not in', repeated_move_line_ids))

        line_ids = line_obj.search(cr, uid, args,
            context=context)

        model_data_ids = mod_obj.search(cr, uid, [('model', '=', 'ir.ui.view'), ('name', '=', 'view_account_statement_from_invoice_lines')], context=context)
        resource_id = mod_obj.read(cr, uid, model_data_ids, fields=['res_id'], context=context)[0]['res_id']
        return {
            'domain': "[('id','in', ["+','.join([str(x) for x in line_ids])+"])]",
            'name': _('Import Entries'),
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.statement.from.invoice.lines',
            'views': [(resource_id,'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

account_statement_from_invoice()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
