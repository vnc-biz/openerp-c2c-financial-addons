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
import logging

from openerp.osv.orm import Model, fields
import pooler
#from datetime import datetime

logger = logging.getLogger('credit.line.management')

class CreditManagementLine (Model):
    """A credit Management line decribe a line of amount due by a customer.
    It is linked to all required financial account.
    It has various state draft open to be send send. For more information about
    usage please read __openerp__.py file"""

    _name = "credit.management.line"
    _description = """A credit Management line"""
    _rec_name = "id"

    _columns = {'date': fields.date('Controlling date', required=True),
                # maturity date of related move line we do not use a related field in order to
                # allow manual changes
                'date_due': fields.date('Due date',
                                        required=True,
                                        readonly=True,
                                        states={'draft': [('readonly', False)]}),

                'date_sent': fields.date('Sent date',
                                         readonly=True,
                                         states={'draft': [('readonly', False)]}),

                'state': fields.selection([('draft', 'Draft'),
                                           ('to_be_sent', 'To be sent'),
                                           ('sent', 'Done')],
                                          'State', required=True, readonly=True),

                'canal': fields.selection([('manual', 'Manual'),
                                           ('mail', 'Mail')],
                                          'Canal', required=True,
                                          readonly=True,
                                          states={'draft': [('readonly', False)]}),

                'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
                'partner_id': fields.many2one('res.partner', "Partner", required=True),
                'amount_due': fields.float('Due Amount Tax inc.', required=True, readonly=True),
                'balance_due': fields.float('Due balance', required=True, readonly=True),
                'mail_id': fields.many2one('mail.thread', 'Sent mail', readonly=True),
                'mail_status': fields.selection([('none', 'None'),
                                                 ('error', 'Error'),
                                                 ('sent', 'Done')],
                                                'Mail status',
                                                readonly=True),

                'move_line_id': fields.many2one('account.move.line', 'Move line',
                                                required=True, readonly=True),

                'account_id': fields.related('move_line_id', 'account_id', type='many2one',
                                             relation='account.account', string='Account',
                                             store=True, readonly=True),

                # we can allow a manual change of profile in draft state
                'profile_rule_id':fields.many2one('credit.management.profile.rule',
                                                  'Overdue Rule', required=True, readonly=True,
                                                  states={'draft': [('readonly', False)]}),

                'profile_id': fields.related('profile_rule_id', 'profile_id', type='many2one',
                                             relation='credit.management.profile', string='Profile',
                                             store=True, readonly=True),

                'level': fields.related('profile_rule_id', 'level', type='float',
                                         relation='credit.management.profile', string='Level',
                                         store=True, readonly=True),
                # Maybe it should be a related fields of move line company_id
                'company_id': fields.many2one('res.company', 'Company')}

    _defaults = {'state': 'draft',
                 'company_id': lambda s, cr, uid, c: s.pool.get('res.company')._company_default_get(
                                      cr, uid, 'res.partner.address', context=c),}

    def _update_from_mv_line(self, cursor, uid, ids, mv_line_br, rule_br,
                             lookup_date, context=None):
        """hook function to update line if required"""
        context =  context or {}
        return []

    def _create_from_mv_line(self, cursor, uid, ids, mv_line_br,
                             rule_br, lookup_date, context=None):
        """Create credit line"""
        acc_line_obj = self.pool.get('account.move.line')
        context = context or {}
        data_dict = {}
        data_dict['date'] = lookup_date
        data_dict['date_due'] = mv_line_br.date_maturity
        data_dict['state'] = 'draft'
        data_dict['canal'] = rule_br.canal
        data_dict['invoice_id'] = (mv_line_br.invoice_id and mv_line_br.invoice_id.id
                                   or False)
        data_dict['partner_id'] = mv_line_br.partner_id.id
        data_dict['amount_due'] = (mv_line_br.amount_currency or mv_line_br.debit
                                   or mv_line_br.credit)
        data_dict['balance_due'] = acc_line_obj._amount_residual_from_date(cursor, uid, mv_line_br,
                                                                      lookup_date, context=context)
        data_dict['profile_rule_id'] = rule_br.id
        data_dict['company_id'] = mv_line_br.company_id.id
        data_dict['move_line_id'] = mv_line_br.id
        data_dict['mail_status'] = 'none'
        return [self.create(cursor, uid, data_dict)]


    def create_or_update_from_mv_lines(self, cursor, uid, ids, lines,
                                       rule_id, lookup_date, context=None):
        """Create or update line base on rules"""
        context = context or {}
        rule_obj = self.pool.get('credit.management.profile.rule')
        ml_obj = self.pool.get('account.move.line')
        rule = rule_obj.browse(cursor, uid, rule_id, context)
        current_lvl = rule.level
        credit_line_ids = []
        errors =  []
        existings = self.search(cursor, uid, [('move_line_id', 'in', lines),
                                              ('level', '=', current_lvl)])
        for line in ml_obj.browse(cursor, uid, lines, context):
            # we want to create as many line as possible
            db, pool = pooler.get_db_and_pool(cursor.dbname)
            local_cr = db.cursor()
            try:
                if line.id in existings:
                    # does nothing just a hook
                    credit_line_ids += self._update_from_mv_line(local_cr, uid, ids,
                                                                 line, rule, lookup_date,
                                                                 context=context)
                else:
                    credit_line_ids += self._create_from_mv_line(local_cr, uid, ids,
                                                                 line, rule, lookup_date,
                                                                 context=context)
            except Exception, exc:
                logger.error(exc)
                errors.append(unicode(exc))
                local_cr.rollback()
            finally:
                local_cr.commit()
                local_cr.close()
            return (credit_line_ids, errors)
