# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Joel Grand-Guillaume
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

from osv import fields, osv
from tools.translate import _
from account_statement_import.file_parser.parser import FileParser
import datetime
import netsvc
logger = netsvc.Logger()

class CreditStatementImportConfig(osv.osv):
    _name = "credit.statement.import.config"
    _description = __doc__
    _columns = {
        'name': fields.char('Name', size=128, required=True),
        'partner_id': fields.many2one('res.partner',
                                      'Credit insitute partner',
                                      required=True),
        'journal_id': fields.many2one('account.journal',
                                      'Financial journal to use for transaction',
                                      required=True),
        'commission_account_id': fields.many2one('account.account',
                                                         'Commission account',
                                                         required=True),
        'receivable_account_id': fields.many2one('account.account',
                                                        'Force Receivable/Payable Account',
                                                        help="Choose a receivable account to force the default\
                                                        debit/credit account (eg. an intermediat bank account instead of\
                                                        default debitors)."),
                
        'mode': fields.selection([('transaction_id', 'Based on transaction id'),
                                  ('origin', 'Based on order number')],
                                 string="Mode",
                                 required=True)
    }

    _defaults = {'mode': lambda *x: 'transaction_id' }




class AccountSatement(osv.osv):
    """Override account statement to add import."""

    _inherit = "account.bank.statement"
    
    def _get_default_statement_type(self,cr,uid,context=None):
        """Return standard as type unless the key statement_type is in the context."""
        if not context:
            context = {}
        if 'statement_type' in context:
            return context.get('statement_type')
        else:
            return 'standard'
    
    _columns = {
        'import_config_id': fields.many2one('credit.statement.import.config',
                                  'Configuration parameter'),
        'credit_partner_id': fields.related('partner_id', 'credit_partner_id', type='many2one', relation='res.partner', string='Financial Partner', store=True, readonly=True),
        'statement_type': fields.selection(
                        [
                            ('standard', 'Standard'),
                            ('credit_partner', 'Credit card'),
                        ],
                        'Statement type',
                        readonly=True

        ),
        'ref': fields.char('Ref.', size=64, states={'draft': [('readonly', False)]}, readonly=True),
    }

    _defaults = {
        'statement_type': _get_default_statement_type
    }

    def init(self, cr):
        cr.execute("UPDATE account_move_line"
                   " SET ref = replace(ref, 'STAT_TRANS_ID_', 'TID_')"
                   " WHERE ref LIKE 'STAT_TRANS_ID_%';")
        return True

    def _get_line_to_reconcile(self, cursor, uid,
            amount, inv_id, context=None):
        """return the line to reconcile"""
        invoice_obj = self.pool.get('account.invoice')
        invoice = invoice_obj.browse(cursor, uid, inv_id)
        move_line_ids = []
        if not invoice.move_id:
            return []
        for line in invoice.move_id.line_id:
            if line.reconcile_id:
                continue
            if (line.account_id.type in ['receivable', 'payable'] and
                line.account_id.reconcile):
                move_line_ids.append(line.id)
        return move_line_ids

    def get_partner_from_so(self, cursor, uid,
            transaction_id,
            mode='transaction_id'):
        so_obj = self.pool.get('sale.order')
        search_crit = [(mode, '=', transaction_id)]
        so_id = so_obj.search(cursor, uid, search_crit)
        if so_id and len(so_id) == 1:
            return so_obj.browse(cursor, uid, so_id[0]).partner_id.id
        else:
            return False


    def get_default_accounts(self, cursor, uid, receivable_account_id, context=None):
        """We try to determine default accounts if not receivable_account_id set, otherwise
        take it for both receivable and payable account"""
        # TODO find a cleaner way to do it
        account_receivable = False
        account_payable = False
        if receivable_account_id:
            account_receivable = account_payable = receivable_account_id
        else:
            context = context or {}
            property_obj = self.pool.get('ir.property')
            model_fields_obj = self.pool.get('ir.model.fields')
            model_fields_ids = model_fields_obj.search(
                cursor,
                uid,
                [('name', 'in', ['property_account_receivable',
                                 'property_account_payable']),
                 ('model', '=', 'res.partner'),],
                context=context
            )
            property_ids = property_obj.search(
                        cursor,
                        uid, [
                                ('fields_id', 'in', model_fields_ids),
                                ('res_id', '=', False),
                            ],
                        context=context
            )

            
            for erp_property in property_obj.browse(cursor, uid,
                property_ids, context=context):
                if erp_property.fields_id.name == 'property_account_receivable':
                    account_receivable = erp_property.value_reference.id
                elif erp_property.fields_id.name == 'property_account_payable':
                    account_payable = erp_property.value_reference.id
        return account_receivable, account_payable

    def _get_account_id(self, cursor, uid,
            amount, account_receivable, account_payable):
        "return the default account to be used by statement line"
        account_id = False
        if amount >= 0:
            account_id = account_receivable
        else:
            account_id = account_payable
        if not account_id:
            raise osv.except_osv(
                _('Can not determine account'),
                _('Please ensure that minimal properties are set')
            )
        return account_id

    def balance_check(self, cr, uid, st_id, journal_type='bank', context=None):
        """If standard bank statement check the balance, otherwise not."""
        st = self.browse(cr, uid, st_id, context=context)
        if st.statement_type == 'standard':
            return super(AccountSatement, self).balance_check(cr, uid, st_id, journal_type, context)
        else:
            return True


    def credit_statement_import(self, cursor, uid, ids,
                                partner_id,
                                journal_id,
                                commission_account_id,
                                receivable_account_id,
                                file_stream,
                                ftype="csv",
                                mode='transaction_id',
                                context=None):
        "Create statement from file stream encoded in base 64"
        context = context or {}
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        attachment_obj = self.pool.get('ir.attachment')

        account_receivable, account_payable = self.get_default_accounts(cursor, uid, receivable_account_id)

        ##Order of cols does not matter but first row has to be header
        keys = ['transaction_id', 'label', 'date', 'amount', 'commission_amount']
        #required_values = ['transaction_id', 'amount', 'commission_amount']
        convertion_dict = {
                            'transaction_id': unicode,
                            'label': unicode,
                            'date': datetime.datetime,
                            'amount': float,
                            'commission_amount': float
        }

        f_parser = FileParser(file_stream,
                              keys_to_validate=keys,
                              decode_base_64=True,
                              ftype=ftype)
        statement_lines = f_parser.parse()
        statement_lines = f_parser.cast_rows(statement_lines, convertion_dict)
        journal = self.pool.get('account.journal').browse(cursor, uid, journal_id)
        statement_id = statement_obj.create(cursor,
                                            uid,
                                            {
                                                'journal_id': journal_id,
                                                'credit_partner_id': partner_id,
                                                'statement_type': 'credit_partner',
                                            },
                                            context)
        commission_global_amount = 0.0
        if not journal.default_debit_account_id \
           or not journal.default_credit_account_id:
            raise osv.except_osv(
                    _("Missing default account on journal %s")%(journal.name),
                    _("Please correct the journal"))
        try:
            for line in statement_lines:
                line_partner_id = False
                line_to_reconcile = False
                # We ensure that required values of the line are set
#                for val in required_values:
#                    if not line.get(val, False) and line.get(val, False) != 0.0:
#                        raise osv.except_osv(
#                               _("Field %s not set for line %s")%(str(line),),
#                               _("Please correct the file"))

                commission_global_amount += line.get('commission_amount', 0.0)
                values = {
                    'name': "IN %s %s"%(line['transaction_id'],
                                        line.get('label', '')),
                    'date': line.get('date', datetime.datetime.now().date()),
                    'amount': line['amount'],
                    'ref': "TID_%s"%(line['transaction_id'],),
                    'type': 'customer',
                    'statement_id': statement_id,
                    #'account_id': journal.default_debit_account_id
                }
                #TODO => take receivable_account_id into account !
                values['account_id'] = self._get_account_id(
                        cursor,
                        uid,
                        line['amount'],
                        account_receivable,
                        account_payable
                )
                if not line_partner_id:
                    line_partner_id = self.get_partner_from_so(cursor,
                        uid, line['transaction_id'], mode)
                values['partner_id'] = line_partner_id
                # we finally create the line in system
                statement_line_obj.create(cursor, uid, values, context=context)

            # we create commission line
            if commission_global_amount:
                comm_values = {
                    'name': 'IN '+ _('Commission line'),
                    'date': datetime.datetime.now().date(),
                    'amount': commission_global_amount,
                    'partner_id': partner_id,
                    'type': 'general',
                    'statement_id': statement_id,
                    'account_id': commission_account_id,
                    'ref': 'commission'
                }
                statement_line_obj.create(cursor, uid,
                        comm_values, 
                        context=context)

            attachment_obj.create(
                cursor,
                uid,
                {
                    'name': 'statement file',
                    'datas': file_stream,
                    'datas_fname': "%s.%s"%(datetime.datetime.now().date(),
                                            ftype),
                    'res_model': 'account.bank.statement',
                    'res_id': statement_id,
                },
                context=context
            )
        except Exception, exc:
            logger.notifyChannel("Statement import",
                                 netsvc.LOG_ERROR,
                                 _("Statement can not be created %s") %(exc,))

            statement_obj.unlink(cursor, uid, [statement_id])
            raise exc
        return statement_id

class account_bank_statement_line(osv.osv):
    _inherit = "account.bank.statement.line"

    def onchange_partner_id(self, cr, uid, ids, partner_id, context=None):
        if context is None:
            context = {}
        res = super(account_bank_statement_line,self).onchange_partner_id(cr, uid, ids, partner_id, context)
        if 'statement_config' in context:
            c = self.pool.get("credit.statement.import.config").browse(cr,uid,context['statement_config'])
            res['value'].update({'account_id':c.receivable_account_id})
        return res

    def onchange_type(self, cr, uid, line_id, partner_id, type, context=None):
        if context is None:
            context = {}
        res = super(account_bank_statement_line,self).onchange_type(cr, uid, ids, line_id, partner_id, type, context)
        if 'statement_config' in context:
            c = self.pool.get("credit.statement.import.config").browse(cr,uid,context['statement_config'])
            res['value'].update({'account_id':c.receivable_account_id})
        return res

            