# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
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

from osv import osv, fields


class account_fiscal_position_rule(osv.osv):

    _inherit = "account.fiscal.position.rule"

    _columns = {
        'partner_fiscal_category_id': fields.many2one(
            'res.partner.category', 'Partner Fiscal Category'),
    }

    def _map_domain(self, cr, uid, partner,
                    partner_address, company, context=None):
        domain = super(account_fiscal_position_rule, self)._map_domain(
            cr, uid, partner, partner_address, company, context=context)

        if partner.fiscal_category_id:
            domain += \
            ('|',
            ('partner_fiscal_category_id', '=', partner.fiscal_category_id.id),
            )

        domain += (('partner_fiscal_category_id', '=', False), )
        return domain

account_fiscal_position_rule()


class account_fiscal_position_rule_template(osv.osv):

    _inherit = "account.fiscal.position.rule.template"

    _columns = {
        'partner_fiscal_category_id': fields.many2one(
            'res.partner.category', 'Partner Fiscal Category'),
        }

account_fiscal_position_rule_template()


class wizard_account_fiscal_position_rule(osv.osv_memory):

    _inherit = 'wizard.account.fiscal.position.rule'

    def _template_vals(self, cr, uid, template, company_id,
                       fiscal_position_ids, context=None):
        vals = super(wizard_account_fiscal_position_rule, self)._template_vals(
            cr, uid, template, company_id, fiscal_position_ids, context=context
        )
        vals['partner_fiscal_category_id'] = \
            template.partner_fiscal_category_id
        return vals

wizard_account_fiscal_position_rule()
