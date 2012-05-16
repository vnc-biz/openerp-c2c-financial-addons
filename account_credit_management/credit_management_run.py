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


class CreditManagementRun(Model):
    """Credit management run generate all credit management lines and reject"""

    _name = "credit.management.run"
    _rec_name = 'date'
    _description = """Credit management line generator"""
    _columns = {'date': fields.date('Lookup date'),
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

    def generate_credit_lines(self, cursor, uid, run_id, context=None):
        """Generate credit management lines"""
        context = context or {}
        cr_line_obj = self.pool.get('credit.management.line')
        if isinstance(run_id, list):
            run_id = run_id[0]
        run = self.browse(cursor, uid, run_id, context=context)
        report = []
        profile_ids = run.profile_ids
        if not profile_ids:
            profile_obj = self.pool.get('credit.management.profile')
            profile_ids_ids = profile_obj.search(cursor, uid, [])
            profile_ids =  profile_obj.browse(cursor, uid, profile_ids_ids)
        for profile in profile_ids:
            if profile.do_nothing:
                continue
            #try:
            lines = profile._get_moves_line_to_process(run.date, context=context)
            if not lines:
                continue
            # profile rules are sorted by level so iteration is in the correct order
            for rule in profile.profile_rule_ids:
                rule.get_rule_lines(run.date, lines)
                cr_line_obj._create_or_update_from_mv_lines(lines, rule.id, context=context)
            #except Exception, exc:
                #report.append(unicode(exc))
        return False
