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
        'partner_id': fields.many2one('res.partner',
                                      'Credit insitute partner',
                                      required=True),
        'journal_id': fields.many2one('account.journal',
                                      'Financial journal to use transaction',
                                      required=True),
        #'label': fields.char('Label', size=64, required=True),
        'input_statement': fields.binary('Statement file', required=True),
        'file_name': fields.char('File Name', size=128),
        'commission_account_id': fields.many2one('account.account',
                                                 'Commission account',
                                                 required=True),
        'mode': fields.selection([('transaction_id', 'Based on transaction id'),
                                  ('origin', 'Based on order number')],
                                 string="Mode",
                                 required=True)
    }

    _defaults = {'mode': lambda *x: 'transaction_id' }


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
                                            importer.partner_id.id,
                                            importer.journal_id.id,
                                            importer.commission_account_id.id,
                                            importer.input_statement,
                                            ftype.replace('.',''),
                                            mode=importer.mode,
                                            context=context
        )
        return {'statement_id': sid}

