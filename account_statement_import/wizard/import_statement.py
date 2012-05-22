# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
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

"""
Wizard to import financial institute date in bank statement
"""

from osv import fields, osv
from tools.translate import _
import os

class CreditPartnerStatementImporter(osv.osv_memory):
    """Import Credit statement"""

    _name = "credit.statement.import"
    _description = __doc__
    _columns = {
        
        'import_config_id': fields.many2one('credit.statement.import.config',
                                      'Import configuration parameter',
                                      required=True),
        'partner_id': fields.many2one('res.partner',
                                      'Credit insitute partner',
                                      ),
        'journal_id': fields.many2one('account.journal',
                                      'Financial journal to use transaction',
                                      ),
        'input_statement': fields.binary('Statement file', required=True),
        'file_name': fields.char('File Name', size=128),
        'commission_account_id': fields.many2one('account.account',
                                                 'Commission account',
                                                 ),
        'receivable_account_id': fields.many2one('account.account',
                                                 'Force Receivable/Payable Account'),
        'mode': fields.selection([('transaction_id', 'Based on transaction id'),
                                  ('origin', 'Based on order number')],
                                 string="Mode",
                                 )
    }

    _defaults = {'mode': lambda *x: 'transaction_id' }

    def onchange_import_config_id(self, cr, uid, ids, import_config_id, context=None):
        res={}
        if import_config_id:
            c = self.pool.get("credit.statement.import.config").browse(cr,uid,import_config_id)
            res = {'value': {'partner_id': c.partner_id.id, 'journal_id': c.journal_id.id, 'commission_account_id': \
                    c.commission_account_id.id, 'receivable_account_id': c.receivable_account_id and c.receivable_account_id.id or False,
                    'mode':c.mode}}
        return res

    def import_statement(self, cursor, uid, req_id, context=None):
        """This Function import credit card agency statement"""
        context = context or {}
        if isinstance(req_id, list):
            req_id = req_id[0]
        importer = self.browse(cursor, uid, req_id, context)
        (shortname, ftype) = os.path.splitext(importer.file_name)
        if not ftype:
            #We do not use osv exception we do not want to have it logged
            raise Exception(_('Please use a file with an extention'))
        sid = self.pool.get(
                'account.bank.statement').credit_statement_import(
                                            cursor,
                                            uid,
                                            False,
                                            importer.import_config_id.id,
                                            importer.input_statement,
                                            ftype.replace('.',''),
                                            context=context
        )
        obj_data = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = obj_data.get_object_reference(cursor, uid, 'account_statement_import', 'action_treasury_statement_tree')
        
        id = result and result[1] or False
        result = act_obj.read(cursor, uid, [id], context=context)[0]
        result['domain'] = str([('id','in',[sid])])
        return result
