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
import netsvc
logger = netsvc.Logger()
from openerp.osv.orm import Model, fields
from openerp.addons.account_statement_base_completion.statement import ErrorTooManyPartner


class AccountStatementCompletionRule(Model):
    """This will represent all the completion method that we can have to
    fullfill the bank statement. You'll be able to extend them in you own module
    and choose those to apply for every statement profile.
    The goal of a rules is to fullfill at least the partner of the line, but
    if possible also the reference because we'll use it in the reconciliation 
    process. The reference should contain the invoice number or the SO number
    """
    
    _inherit = "account.statement.completion.rule"
    
    def _get_functions(self):
        res = super (self,AccountStatementCompletionRule)._get_functions()
        res.append(('get_from_ref_and_so', 'From line reference (based on SO number)'))
        return res
    
    _columns={
        'function_to_call': fields.selection(_get_functions, 'Method'),
    }

    def get_from_ref_and_so(self, cursor, uid, line_id, context=None):
        """Match the partner based on the SO number and the reference of the statement 
        line. Then, call the generic st_line method to complete other values. In that
        case, we always fullfill the reference of the line with the SO name
        If more than one partner matched, raise an error.
        Return:
            A dict of value that can be passed directly to the write method of
            the statement line.
           {'partner_id': value,
            'account_id' : value,
            ...}
        """
        st_obj = self.pool.get('account.bank.statement.line')
        st_line = st_obj.browse(cr,uid,line_id)
        res = {}
        if st_line:
            so_obj = self.pool.get('sale.order')
            so_id = so_obj.search(cursor, uid, [('name', '=', st_line.ref)])
            if so_id and len(so_id) == 1:
                so = so_obj.browse(cursor, uid, so_id[0])
                res['partner_id'] = so.partner_id.id
                res['ref'] = so.name
            elif so_id and len(so_id) > 1:
                raise ErrorTooManyPartner(_('Line named "%s" was matched by more than one partner.')%(st_line.name,st_line.id))
            st_vals = st_obj.get_values_for_line(cr, uid, profile_id = st_line.statement_id.profile_id.id,
                partner_id = res.get('partner_id',False), line_type = st_line.type, st_line.amount, context)
            res.update(st_vals)
        return res


