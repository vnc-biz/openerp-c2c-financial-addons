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

from osv import osv, fields
import netsvc


class payment_order(osv.osv):
    _inherit = 'payment.order'
    ### It will set the date 
    def action_open(self, cr, uid, ids, *args):
        return_code = super(payment_order,self).action_open(cr, uid, ids, args)
        payment_line_obj = self.pool.get('payment.line')
        if return_code:
            for order in self.browse(cr,uid,ids):
            ### In the case of a date prefered to Directy , we set the current date into the bank statement
                if order.date_prefered == 'now':
                    for line in order.line_ids:
                        ## in case of no date defined on line
                        if not line.date:
                            payment_line_obj.write(cr, uid, [line.id], {'date': time.strftime('%Y-%m-%d')})
        return return_code

payment_order()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
