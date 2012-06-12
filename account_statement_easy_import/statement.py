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

from tools.translate import _
from account_statement_ext.file_parser.parser import FileParser
import datetime
import netsvc
logger = netsvc.Logger()
from openerp.osv.orm import Model, fields


class AccountBankSatement(Model):

    _inherit = "account.bank.statement"
 
    def get_partner_from_so(self, cursor, uid,transaction_id):
        """Look for the SO that has the given transaction_id, if not
        found, try to match the SO name instead. If still nothing, 
        return False"""
        so_obj = self.pool.get('sale.order')
        so_id = so_obj.search(cursor, uid, [('transaction_id', '=', transaction_id)])
        if so_id and len(so_id) == 1:
            return so_obj.browse(cursor, uid, so_id[0]).partner_id.id
        else:
            so_id2 = so_obj.search(cursor, uid, [('name', '=', transaction_id)])
            if so_id2 and len(so_id2) == 1:
                return so_obj.browse(cursor, uid, so_id2[0]).partner_id.id
        return False


    def _get_value_from_import_config(self, cr, uid, profile_id):
        """Return a dict with with values taken from the given config. 
        e.g. (journal_id, partner_id, commission_account_id, mode, forced_account_id)
        """
        # Get variable from config
        import_config = self.pool.get("account.statement.profil").browse(cr,uid,profile_id)
        forced_account_id = import_config.receivable_account_id and import_config.receivable_account_id.id or False
        journal_id = import_config.journal_id and import_config.journal_id.id or False
        partner_id = import_config.partner_id and import_config.partner_id.id or False
        commission_account_id = import_config.commission_account_id.id
        commission_analytic_id = import_config.commission_analytic_id and import_config.commission_analytic_id.id or False
        force_partner_on_bank = import_config.force_partner_on_bank
        return journal_id, partner_id, commission_account_id, commission_analytic_id, forced_account_id, force_partner_on_bank

    def statement_import(self, cursor, uid, ids,
                                profile_id,
                                file_stream,
                                ftype="csv",
                                context=None):
        "Create statement from file stream encoded in base 64."
        context = context or {}
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        attachment_obj = self.pool.get('ir.attachment')
        
        # Get variable from config
        journal_id, partner_id, commission_account_id, commission_analytic_id, \
            forced_account_id, force_partner_on_bank = self._get_value_from_import_config(cursor,uid,profile_id)

        account_receivable, account_payable = self.get_default_pay_receiv_accounts(cursor, uid, forced_account_id)

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
                                            {   'profile_id':profile_id,
                                                'journal_id': journal_id,
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
                values['account_id'] = self.get_account_for_counterpart(
                        cursor,
                        uid,
                        line['amount'],
                        account_receivable,
                        account_payable
                )
                if not line_partner_id:
                    line_partner_id = self.get_partner_from_so(cursor,
                        uid, line['transaction_id'])
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
                    'ref': 'commission',
                    'analytic_account_id': commission_analytic_id
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


