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
from openerp.osv.orm import Model, fields

class CreditManagementRun (Model):
    """Credit management run generate all credit management lines and reject"""

    _name = "credit.management.run"
    _description = """Credit management line generator"""
    _columns = {'name': fields.date('Lookup date'),
                'profile_ids': fields.many2many('credit.management.profile',
                                                rel="credit_run_profile_rel",
                                                string='Profiles',
                                                readonly=True,
                                                states={'draft': [('readonly', False)]}),
                'rejected_ids': fields.many2many('account.move.line',
                                                 rel="credit_runreject_rel",
                                                 string='Non evaluated lines',
                                                 readonly=True),
                'report': fields.text('Report', readonly=True),

                'state': fields.selection([('draft', 'Draft'),
                                            ('running', 'Running'),
                                            ('done', 'Done'),
                                            ('error', 'Error')],
                                           string='State',
                                           required=True,
                                           readonly=True)}

    _defaults = {'state': 'draft'}

    def generate_credit_lines(self, cursor, uid, ids, optional_args, context=None):
        context = context or {}
        if isinstance(ids, (int, long)):
            ids = [ids]
        # TODO
        return False
