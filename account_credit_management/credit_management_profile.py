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


    def _get_account_related_lines(self, cursor, uid, profile_id, lookup_date, lines, context=None):
        """ We get all the lines related to accounts with given credit profile.
            We try not to use direct SQL in order to respect security rules.
            As we define the first set it is important"""
        context = context or {}
        move_l_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        acc_ids =  account_obj.search(cursor, uid, [('credit_profile_id', '=', profile_id)])
        if not acc_ids:
            return lines
        move_ids =  move_l_obj.search(cursor, uid, [('account_id', 'in', acc_ids),
                                                    ('maturity_date', '<=', lookup_date),
                                                    ('reconcile_id', '=', False),
                                                    ('partner_id', '!=', False)])

        lines += move_ids
        return lines


    def _get_sum_reduce_range(self, cursor, uid, profile_id, lookup_date, lines, model,
                              move_relation_field, context=None):
        """ We get all the lines related to the model with given credit profile.
            We also reduce from the global set (lines) the move line to be excluded.
            We try not to use direct SQL in order to respect security rules.
            As we define the first set it is important.
            The profile relation field MUST be named credit_profile_id
            and the model must have a relation
            with account move line"""
        # MARK possible place for a good optimisation
        context = context or {}
        my_obj = self.pool.get('res.partner')
        move_l_obj = self.pool.get('account.move.line')
        add_obj_ids =  my_obj.search(cursor, uid, [('credit_profile_id', '=', profile_id)])
        if add_obj_ids:
            add_lines = move_l_obj.search(cursor, uid, [(move_relation_field, 'in', add_obj_ids),
                                                        ('maturity_date', '<=', lookup_date),
                                                        ('partner_id', '!=', False),
                                                        ('reconcile_id', '=', False)])
            lines = list[set(lines + add_lines)]
        # we get all the lines that must be excluded at partner_level
        # from the global set (even the one included at account level)
        neg_obj_ids =  my_obj.search(cursor, uid, [('credit_profile_id', '!=', profile_id),
                                                   ('credit_profile_id', '!=', False)])
        if neg_obj_ids:
            # should we add ('id', 'in', lines) in domain ? it may give a veeery long SQL...
            neg_lines = move_l_obj.search(cursor, uid, [(move_relation_field, 'in', neg_obj_ids),
                                                        ('maturity_date', '<=', lookup_date),
                                                        ('partner_id', '!=', False),
                                                        ('reconcile_id', '=', False)])
            if neg_lines:
                lines = list(set(lines) - set(neg_lines))
        return lines


    def _get_partner_related_lines(self, cursor, uid, profile_id, lookup_date, lines, context=None):
        return self._get_sum_reduce_range(self, cursor, uid, profile_id, lookup_date, lines,
                                          'res.partner', 'partner_id', context=context)



    def _get_invoice_related_lines(self, cursor, uid, profile_id, lookup_date, lines, context=None):
        return self._get_sum_reduce_range(self, cursor, uid, profile_id, lookup_date, lines,
                                          'account.invoice', 'invoice', context=context)





    def _get_moves_line_to_process(self, cursor, uid, profile_id, lookup_date, context=None):
        """Retrive all the move line to be procces for current profile.
           This function is planned to be use only on one id.
           Priority of inclustion, exlusion is account, partner, invoice"""
        context = context or {}
        lines = []
        if isinstance(profile_id, list):
            profile_id = profile_id[0]
        # order of call MUST be respected priority is account, partner, invoice
        self._get_account_related_lines(cursor, profile_id, uid, lookup_date, lines, context=context)
        self._get_partner_related_lines(cursor, profile_id, uid, lookup_date, lines, context=context)
        self._get_invoice_related_lines(cursor, profile_id, uid, lookup_date, lines, context=context)
        print lines




class CreditManagementProfileRule (Model):
    """Define a profile rule. A rule allows to determine if
    a move line is due and the level of overdue of the line"""

    _name = "credit.management.profile.rule"
    _order = 'level'
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

                'delay_days': fields.integer('Delay in day', required='True'),
                'mail_template_id': fields.many2one('email.template', 'Mail template',
                                                    required=True),
                }



    def _check_level_mode(self, cursor, uid, rids, context=None):
        """We check that the smallest level is not base on previous rules"""
        if not isinstance(rids, list):
            rids = [rids]
        for rule in self.browse(cursor, uid, rids, context):
            smallest_rule_id = self.search(cursor, uid, [('profile_id', '=', rule.profile_id.id)],
                                           order='level desc', limit=1, context=context)
            smallest_rule = self.browse(cursor, uid, smallest_rule_id[0], context)
            if smallest_rule.computation_mode == 'previous_date':
                return False
        return True



    _sql_constraint = [('unique level',
                        'UNIQUE (profile_id, level)',
                        'Level must be unique per profile')]

    _constraints = [(_check_level_mode,
                     'The smallest level can not be of type Previous reminder',
                     ['level'])]
