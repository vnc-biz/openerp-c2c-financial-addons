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

class CreditManagementProfile(Model):
    """Define a profile of reminder"""

    _name = "credit.management.profile"
    _description = """Define a reminder profile"""
    _columns = {'name': fields.char('Name', required=True, size=128),
                'profile_rule_ids' : fields.one2many('credit.management.profile.rule',
                                                     'profile_id',
                                                     'Profile Rules'),
                'do_nothing' : fields.boolean('Do nothing',
                                              help=('For profiling who should not '
                                                    'generate lines or are obsolete')),
                }



class CreditManagementProfileRule (Model):
    """Define a profile rule. A rule allows to determine if
    a move line is due and the level of overdue of the line"""

    _name = "credit.management.profile.rule"
    _description = """A credit management profile rule"""
    _columns = {'profile_id': fields.many2one('credit.management.profile',
                                              'Related Policy', required=True),
                'name': fields.char('Name', size=128, required=True),
                'level': fields.float('level', required=True),
                'computation_mode': fields.selection([('net_days', 'Net days'),
                                                      ('end_of_month', 'End of Month'),
                                                      ('previous_date', 'Previous reminder')],
                                                     'Compute mode',
                                                     required=True),
                'delay_days': fields.integer('Delay in day', required='True')}



    def _check_level_mode(self, cursor, uid, rids, context=None):
        if not isinstance(rids, list):
            rids = [rids]
        for rule in self.browse(cursor, uid, rids, context):
            smallest_rule_id = self.search(cursor, uid, [('profile_id', '=', rule.profile_id)],
                                           order='level desc', limit=1, context=context)
            smallest_rule = self.browse(cursor, uid, smallest_rule_id, context)
            if smallest_rule.computation_mode == 'previous_date':
                return False
        return True



    _sql_constraint = [('unique level',
                        'UNIQUE (profile_id, level)',
                        'Level must be unique per profile')]

    _constraints = [(_check_level_mode,
                     'The smallest level can not be of type Previous reminder',
                     ['level'])]
