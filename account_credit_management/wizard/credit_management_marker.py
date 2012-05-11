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

class CreditManagementMarker(TransientModel):
    """Change the state of lines in mass"""

    _name = "credit.management.marker"
    _description = """Mass marker"""
    _columns = {'name': fields.selection([('to_be_sent', 'To be sent'),
                                          ('sent', 'Done')],
                                          'Mark as', required=True),

                'mark_all': fields.boolean('Mark all draft lines')}

    _defaults = {'name': 'to_be_sent'}

    def mark_lines(self, cursor, uid, ids, optional_args, context=None):
        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        return False
