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

logger = logging.getLogger('Credit management run')

memoizers = {}


class CreditManagementRun(Model):
    """Credit management run generate all credit management lines and reject"""

    _name = "credit.management.run"
    _rec_name = 'date'
    _description = """Credit management line generator"""
    _columns = {'date': fields.date('Lookup date', required=True),
                'profile_ids': fields.many2many('credit.management.profile',
                                                rel="credit_run_profile_rel",
                                                string='Profiles',
                                                readonly=True,
                                                help="If nothing set all profile will be used",

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
                                                string='Line to be handled manually',
                                                readonly=True),
    }

    _defaults = {'state': 'draft'}

    def check_run_date(self, cursor, uid, ids, lookup_date, context=None):
        """Ensure that there is no credit line in the future using lookup_date"""
        line_obj =  self.pool.get('credit.management.line')
        lines = line_obj.search(cursor, uid, [('date', '>', lookup_date)],
                                order='date DESC', limit=1)
        if lines:
            line = line_obj.browse(cursor, uid, lines[0])
            raise except_osv(_('A run was already executed in a greater date'),
                             _('Run date should be >= %s') % (line.date))


    def _generate_credit_lines(self, cursor, uid, run_id, context=None):
        """ Generate credit line. Function can be a little dryer but
        it does almost noting, initalise variable maange error and call
        real know how method"""
        memoizers['credit_line_residuals'] = {}
        cr_line_obj = self.pool.get('credit.management.line')
        if isinstance(run_id, list):
            run_id = run_id[0]
        run = self.browse(cursor, uid, run_id, context=context)
        errors = []
        manualy_managed_lines = [] #line who changed profile
        credit_line_ids = [] # generated lines
        run.check_run_date(run.date, context=context)
        profile_ids = run.profile_ids
        if not profile_ids:
            profile_obj = self.pool.get('credit.management.profile')
            profile_ids_ids = profile_obj.search(cursor, uid, [])
            profile_ids =  profile_obj.browse(cursor, uid, profile_ids_ids)
        for profile in profile_ids:
            if profile.do_nothing:
                continue
            try:
                lines = profile._get_moves_line_to_process(run.date, context=context)
                tmp_manual = profile._check_lines_profiles(lines, context=context)
                lines = list(set(lines) - set(tmp_manual))
                manualy_managed_lines += tmp_manual
                if not lines:
                    continue
                # profile rules are sorted by level so iteration is in the correct order
                for rule in profile.profile_rule_ids:
                    rule_lines = rule.get_rule_lines(run.date, lines)
                    #only this write action own a separate cursor
                    credit_line_ids += cr_line_obj.create_or_update_from_mv_lines(cursor, uid, [],
                                                                                 rule_lines, rule.id,
                                                                                 run.date, errors=errors,
                                                                                 context=context)
                lines = list(set(lines) - set(rule_lines))
            except Exception, exc:
                cursor.rollback()
                error_type, error_value, trbk = sys.exc_info()
                st = "Error: %s\nDescription: %s\nTraceback:" % (error_type.__name__, error_value)
                st += ''.join(traceback.format_tb(trbk, 30))
                logger.error(st)
                self.write(cursor, uid, [run.id], {'report':st, 'state': 'error'})
                return False
            vals = {'report': u"Number of generated lines : %s \n" % (len(credit_line_ids),),
                    'state': 'done',
                    'manual_ids': [(6, 0, manualy_managed_lines)]}
            if errors:
                vals['report'] += u"Following line generation errors appends:"
                vals['report'] += u"----\n".join(errors)
                vals['state'] = 'done'
            run.write(vals)
        # lines will correspond to line that where not treated
        return lines



    def generate_credit_lines(self, cursor, uid, run_id, context=None):
        """Generate credit management lines"""
        context = context or {}
        # we do a little magical tips in order to ensure non concurrent run
        # of the function generate_credit_lines
        try:
            cursor.execute('SELECT id FROM credit_management_run'
                           ' LIMIT 1 FOR UPDATE NOWAIT' )
        except Exception, exc:
            cursor.rollback()
            raise except_osv(_('A credit management run is allready running'
                               ' in background please try later'),
                             str(exc))
        # in case of exception openerp will do a rollback for us and free the lock
        return self._generate_credit_lines(cursor, uid, run_id, context)
