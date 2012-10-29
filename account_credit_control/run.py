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
import sys
import traceback
import logging

from openerp.osv.orm import Model, fields
from openerp.tools.translate import _
from openerp.osv.osv import except_osv

logger = logging.getLogger('Credit Control run')

# beware, do always use the DB lock of `CreditControlRun.generate_credit_lines`
# to use this variable, otherwise you will have race conditions
memoizers = {}


class CreditControlRun(Model):
    """Credit Control run generate all credit control lines and reject"""

    _name = "credit.control.run"
    _rec_name = 'date'
    _description = """Credit control line generator"""
    _columns = {
        'date': fields.date('Controlling Date', required=True),
        'policy_ids': fields.many2many('credit.control.policy',
                                        rel="credit_run_policy_rel",
                                        id1='run_id', id2='policy_id',
                                        string='Policies',
                                        readonly=True,
                                        states={'draft': [('readonly', False)]}),

        'report': fields.text('Report', readonly=True),

        'state': fields.selection([('draft', 'Draft'),
                                   ('running', 'Running'),
                                   ('done', 'Done'),
                                   ('error', 'Error')],
                                   string='State',
                                   required=True,
                                   readonly=True),

        'manual_ids': fields.many2many('account.move.line',
                                        rel="credit_runreject_rel",
                                        string='Lines to handle manually',
                                        readonly=True),
    }

    def _get_policies(self, cursor, uid, context=None):
        return self.pool.get('credit.control.policy').\
                search(cursor, uid, [], context=context)

    _defaults = {
        'state': 'draft',
        'policy_ids': _get_policies,
    }

    def _check_run_date(self, cursor, uid, ids, controlling_date, context=None):
        """Ensure that there is no credit line in the future using controlling_date"""
        line_obj =  self.pool.get('credit.control.line')
        lines = line_obj.search(cursor, uid, [('date', '>', controlling_date)],
                                order='date DESC', limit=1, context=context)
        if lines:
            line = line_obj.browse(cursor, uid, lines[0], context=context)
            raise except_osv(
                _('Error'),
                _('A run has already been executed more recently than %s') % (line.date))
        return True

    def _generate_credit_lines(self, cursor, uid, run_id, context=None):
        """ Generate credit control lines. """
        memoizers['credit_line_residuals'] = {}
        cr_line_obj = self.pool.get('credit.control.line')
        assert not (isinstance(run_id, list) and len(run_id) > 1), \
                "run_id: only one id expected"
        if isinstance(run_id, list):
            run_id = run_id[0]

        run = self.browse(cursor, uid, run_id, context=context)
        errors = []
        manually_managed_lines = set()  # line who changed policy
        credit_line_ids = []  # generated lines
        run._check_run_date(run.date, context=context)

        policies = run.policy_ids
        if not policies:
            raise except_osv(
                _('Error'),
                _('Please select a policy'))

        for policy in policies:
            if policy.do_nothing:
                continue
            lines = policy._get_move_lines_to_process(run.date, context=context)
            manual_lines = policy._lines_different_policy(lines, context=context)
            lines.difference_update(manual_lines)
            manually_managed_lines.update(manual_lines)
            if not lines:
                continue
            # policy levels are sorted by level so iteration is in the correct order
            for level in reversed(policy.level_ids):
                level_lines = level.get_level_lines(run.date, lines, context=context)
                loc_ids, loc_errors = cr_line_obj.create_or_update_from_mv_lines(
                    cursor, uid, [], list(level_lines), level.id, run.date, context=context)
                credit_line_ids += loc_ids
                errors += loc_errors

            lines.difference_update(level_lines)
            vals = {'report': u"Number of generated lines : %s \n" % (len(credit_line_ids),),
                    'manual_ids': [(6, 0, manually_managed_lines)]}

            if errors:
                vals['report'] += u"Following line generation errors appends:"
                vals['report'] += u"----\n".join(errors)

            run.write(vals, context=context)
        run.write({'state': 'done'}, context=context)
        # lines will correspond to line that where not treated
        return lines

    def generate_credit_lines(self, cursor, uid, run_id, context=None):
        """Generate credit control lines

        Lock the ``credit_control_run`` Postgres table to avoid concurrent
        calls of this method.
        """
        if context is None:
            context = {}
        try:
            cursor.execute('SELECT id FROM credit_control_run'
                           ' LIMIT 1 FOR UPDATE NOWAIT' )
        except Exception, exc:
            # in case of exception openerp will do a rollback for us and free the lock
            raise except_osv(
                    _('Error'),
                    _('A credit control run is already running'
                      ' in background, please try later.'), str(exc))

        self._generate_credit_lines(cursor, uid, run_id, context)
        return True

