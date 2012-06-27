# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2010 Camptocamp SA (http://www.camptocamp.com) 
# All Right Reserved
#
# Author : Nicolas Bessi (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import osv, fields
class account_move_line(osv.osv):
    _inherit = "account.move.line"
    
    def _line_balance(self, cr, uid, ids, prop, unknow_none, unknow_dict):
        res={}
        # TODO group the foreach in sql
        for id in ids:
            cr.execute('SELECT debit-credit FROM account_move_line WHERE id=%s ', (id,))
            res[id] = cr.fetchone()[0]
        return res

    _columns = {
        'line_balance': fields.function(_line_balance, method=True, string='Line Balance',
                                        store={'account.move.line': (lambda self, cr, uid, ids, c={}: ids, ['debit','credit'], 20)}),
    }


    
account_move_line()