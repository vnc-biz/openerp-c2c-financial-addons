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
from openerp.osv.orm import  TransientModel, fields

class CreditManagementPrinter(TransientModel):
    """Change the state of lines in mass"""

    _name = "credit.management.printer"
    _rec_name = 'id'
    _description = """Mass printer"""
    _columns = {'mark_as_sent': fields.boolean('Mark lines as send',
                                               help="Lines to emailed will be ignored"),
                'print_all': fields.boolean('Print all ready lines')}


    def print_lines(self, cursor, uid, ids, optional_args, context=None):
        comm_obj = self.pool.get('credit.management.communication')
        context = context or {}
        if isinstance(wiz_id, list):
            wiz_id = wiz_id[0]
        current = self.browse(cursor, uid, wiz_id, context)
        lines_ids = context.get('active_ids')
        if not lines_ids and not current.mail_all:
            raise except_osv(_('Not lines ids are selected'),
                             _('You may check "Print all ready lines"'))
        return False
