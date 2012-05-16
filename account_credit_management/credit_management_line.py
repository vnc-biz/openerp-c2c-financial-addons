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

class CreditManagementLine (Model):
    """A credit Management line decribe a line of amount due by a customer.
    It is linked to all required financial account.
    It has various state draft open to be send send. For more information about
    usage please read __openerp__.py file"""

    _name = "credit.management.line"
    _description = """A credit Management line"""
    _rec_name ="id"

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
                'address_id': fields.many2one('res.partner.address', 'Mail address', required=True),
                'amount_due': fields.float('Due Amount Tax inc.', required=True, readonly=True),
                'balance_due': fields.float('Due balance', required=True, readonly=True),
                'mail_id': fields.many2one('mail.thread', 'Sent mail', readonly=True),

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
                                         relation='credit.management.profile', string='Profile',
                                         store=True, readonly=True),
                'company_id': fields.many2one('res.company', 'Company'),

            }

    _defaults = {'state': 'draft',
                 'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(
                                      cr, uid, 'res.partner.address', context=c),}

    def create_or_update_from_mv_lines(self, cursor, uid, ids, lines, rule_id, context=None):
        print 'TODO'
