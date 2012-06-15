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
from openerp.tools.translate import _

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

                'company_id' : fields.many2one('res.company', 'Company')
                }


    def _get_account_related_lines(self, cursor, uid, profile_id, lookup_date, lines, context=None):
        """ We get all the lines related to accounts with given credit profile.
            We try not to use direct SQL in order to respect security rules.
            As we define the first set it is important, The date is used to do a prefilter.
            !!!We take the asumption that only receivable lines have a maturity date
            and account must be reconcillable"""
        context = context or {}
        move_l_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        acc_ids =  account_obj.search(cursor, uid, [('credit_profile_id', '=', profile_id)])
        if not acc_ids:
            return lines
        move_ids =  move_l_obj.search(cursor, uid, [('account_id', 'in', acc_ids),
                                                    ('date_maturity', '<=', lookup_date),
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
            with account move line.
            !!! We take the asumption that only receivable lines have a maturity date
            and account must be reconcillable"""
        # MARK possible place for a good optimisation
        context = context or {}
        my_obj = self.pool.get(model)
        move_l_obj = self.pool.get('account.move.line')
        add_obj_ids =  my_obj.search(cursor, uid, [('credit_profile_id', '=', profile_id)])
        if add_obj_ids:
            add_lines = move_l_obj.search(cursor, uid, [(move_relation_field, 'in', add_obj_ids),
                                                        ('date_maturity', '<=', lookup_date),
                                                        ('partner_id', '!=', False),
                                                        ('reconcile_id', '=', False)])
            lines = list(set(lines + add_lines))
        # we get all the lines that must be excluded at partner_level
        # from the global set (even the one included at account level)
        neg_obj_ids =  my_obj.search(cursor, uid, [('credit_profile_id', '!=', profile_id),
                                                   ('credit_profile_id', '!=', False)])
        if neg_obj_ids:
            # should we add ('id', 'in', lines) in domain ? it may give a veeery long SQL...
            neg_lines = move_l_obj.search(cursor, uid, [(move_relation_field, 'in', neg_obj_ids),
                                                        ('date_maturity', '<=', lookup_date),
                                                        ('partner_id', '!=', False),
                                                        ('reconcile_id', '=', False)])
            if neg_lines:
                lines = list(set(lines) - set(neg_lines))
        return lines


    def _get_partner_related_lines(self, cursor, uid, profile_id, lookup_date, lines, context=None):
        return self._get_sum_reduce_range(cursor, uid, profile_id, lookup_date, lines,
                                          'res.partner', 'partner_id', context=context)


    def _get_invoice_related_lines(self, cursor, uid, profile_id, lookup_date, lines, context=None):
        return self._get_sum_reduce_range(cursor, uid, profile_id, lookup_date, lines,
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
        lines = self._get_account_related_lines(cursor, uid, profile_id,
                                                lookup_date, lines, context=context)
        lines = self._get_partner_related_lines(cursor, uid, profile_id,
                                                lookup_date, lines, context=context)
        lines = self._get_invoice_related_lines(cursor, uid, profile_id,
                                                lookup_date, lines, context=context)
        return lines

    def _check_lines_profiles(self, cursor, uid, profile_id, lines, context=None):
        """ Check if there is credit line related to same move line but
            related to an other profile"""
        context = context or {}
        if not lines:
            return []
        if isinstance(profile_id, list):
            profile_id = profile_id[0]
        cursor.execute("SELECT move_line_id FROM credit_management_line"
                       " WHERE profile_id != %s and move_line_id in %s",
                       (profile_id, tuple(lines)))
        res = cursor.fetchall()
        if res:
            return [x[0] for x in res]
        else:
            return []



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

                'computation_mode': fields.selection([('net_days', 'Due date'),
                                                      ('end_of_month', 'Due Date: end of Month'),
                                                      ('previous_date', 'Previous reminder')],
                                                     'Compute mode',
                                                     required=True),

                'delay_days': fields.integer('Delay in day', required='True'),
                'mail_template_id': fields.many2one('email.template', 'Mail template',
                                                    required=True),
                'canal': fields.selection([('manual', 'Manual'),
                                           ('mail', 'Mail')],
                                          'Canal', required=True),
                }


    def _check_level_mode(self, cursor, uid, rids, context=None):
        """We check that the smallest level is not based
            on a rule using previous_date mode"""
        if not isinstance(rids, list):
            rids = [rids]
        for rule in self.browse(cursor, uid, rids, context):
            smallest_rule_id = self.search(cursor, uid, [('profile_id', '=', rule.profile_id.id)],
                                           order='level asc', limit=1, context=context)
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

    def _is_first_level(self, cursor, uid, rule_br, context=None):
        """Check if rule has the smallest priority"""
        first_rule = self.search(cursor, uid, [('profile_id', '=', rule_br.profile_id.id)],
                                 order='level asc', limit=1, context=context)
        return first_rule[0] == rule_br.id
    # ----- time related functions ---------

    def _net_days_get_boundary(self):
        return " (mv_line.date_maturity + %(delay)s)::date <= date(%(lookup_date)s)"

    def _end_of_month_get_boundary(self):
        return ("(date_trunc('MONTH', (mv_line.date_maturity + %(delay)s))+INTERVAL '1 MONTH - 1 day')::date"
                "<= date(%(lookup_date)s)")

    def _previous_date_get_boundary(self):
        return "(cr_line.date + %(delay)s)::date <= date(%(lookup_date)s)"

    def _get_sql_date_boundary_for_computation_mode(self, cursor, uid, rule_br, lookup_date, context=None):
        """Return a where clauses statement for the given
           lookup date and computation mode of the rule"""
        fname = "_%s_get_boundary" % (rule_br.computation_mode,)
        if hasattr(self, fname):
            fnc = getattr(self, fname)
            return fnc()
        else:
            raise NotImplementedError(_('Can not get function for computation mode: '
                                        '%s is not implemented') % (fname,))

    # -----------------------------------------

    def _get_first_level_lines(self, cursor, uid, rule_br, lookup_date, lines, context=None):
        if not lines:
            return []
        """Retrieve all the line that are linked to a frist level rules.
           We use Raw SQL for perf. Security rule where applied in
           profile object when line where retrieved"""
        sql = ("SELECT DISTINCT mv_line.id\n"
               " FROM account_move_line mv_line\n"
               " WHERE mv_line.id in %(line_ids)s\n"
               " AND NOT EXISTS (SELECT cr_line.id from credit_management_line cr_line\n"
               "                  WHERE cr_line.move_line_id = mv_line.id)")
        sql += " AND" + self._get_sql_date_boundary_for_computation_mode(cursor,
                                                                           uid, rule_br,
                                                                           lookup_date, context)
        data_dict = {'lookup_date': lookup_date, 'line_ids': tuple(lines),
                     'delay': rule_br.delay_days}

        cursor.execute(sql, data_dict)
        res = cursor.fetchall()
        if not res:
            return []
        return [x[0] for x in res]


    def _get_other_level_lines(self, cursor, uid, rule_br, lookup_date, lines, context=None):
        # We filter line that have a level smaller than current one
        # TODO if code fits need refactor _get_first_level_lines and _get_other_level_lines
        # Code is not DRY
        if not lines:
            return []
        sql = ("SELECT mv_line.id\n"
               " FROM account_move_line mv_line\n"
               " JOIN  credit_management_line cr_line\n"
               " ON (mv_line.id = cr_line.move_line_id)\n"
               " WHERE cr_line.id = (SELECT credit_management_line.id FROM credit_management_line\n"
               "                            WHERE credit_management_line.move_line_id = mv_line.id\n"
               "                              ORDER BY credit_management_line.level desc limit 1)\n"
               " AND cr_line.level < %(level)s\n"
               " AND mv_line.id in %(line_ids)s\n")
        sql += " AND " + self._get_sql_date_boundary_for_computation_mode(cursor,
                                                                          uid, rule_br,
                                                                          lookup_date, context)
        data_dict =  {'lookup_date': lookup_date, 'line_ids': tuple(lines),
                     'delay': rule_br.delay_days, 'level': rule_br.level}

        cursor.execute(sql, data_dict)
        res = cursor.fetchall()
        if not res:
            return []
        return [x[0] for x in res]

    def get_rule_lines(self, cursor, uid, rule_id, lookup_date, lines, context=None):
        """get all move lines in entry lines that match the current rule"""
        if isinstance(rule_id, list):
            rule_id = rule_id[0]
        matching_lines = []
        rule = self.browse(cursor, uid, rule_id, context=context)
        if self._is_first_level(cursor, uid, rule):
            matching_lines += self._get_first_level_lines(cursor, uid, rule, lookup_date,
                                                          lines, context=context)
        else:
            matching_lines += self._get_other_level_lines(cursor, uid, rule, lookup_date,
                                                          lines, context=context)

        return matching_lines
