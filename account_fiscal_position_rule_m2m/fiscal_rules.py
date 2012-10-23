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
        'from_country_ids': fields.many2many(
            'res.country',
            rel='account_fiscal_rule_res_country_from_rel',
            id1='rule_id', id2='country_id',
            string='Origin Countries'),
         'from_state_ids': fields.many2many(
             'res.country.state',
             rel='account_fiscal_rule_state_from_rel',
             id1='rule_id', id2='state_id',
             string='Origin States'),
        'to_country_ids': fields.many2many(
            'res.country',
            rel='account_fiscal_rule_res_country_to_rel',
            id1='rule_id', id2='country_id',
            string='Destination Countries'),
        'to_state_ids': fields.many2many(
            'res.country.state',
            rel='account_fiscal_rule_state_to_rel',
            id1='rule_id', id2='state_id',
            string='Destination States'),
    }

    def init(self, cr):
        migrations = [
        {'rel_table': 'account_fiscal_rule_res_country_to_rel',
         'from_field': 'to_country',
         'rel_field': 'country_id'},
        {'rel_table': 'account_fiscal_rule_state_to_rel',
         'from_field': 'to_state',
         'rel_field': 'state_id'},
        {'rel_table': 'account_fiscal_rule_res_country_from_rel',
         'from_field': 'from_country',
         'rel_field': 'country_id'},
        {'rel_table': 'account_fiscal_rule_state_from_rel',
         'from_field': 'from_state',
         'rel_field': 'state_id'}]
        for migration in migrations:
            cr.execute("INSERT INTO %(rel_table)s "
                       "(rule_id, %(rel_field)s) "
                       "(SELECT id, %(from_field)s FROM "
                       " account_fiscal_position_rule "
                       "WHERE %(from_field)s IS NOT NULL "
                       " AND (id, %(from_field)s) NOT IN "
                       " (SELECT rule_id, %(rel_field)s "
                       "  FROM %(rel_table)s))" % migration)

            cr.execute("UPDATE account_fiscal_position_rule "
                       "SET %(from_field)s = NULL" % migration)

    m2o_replaced_fields = ['from_country',
                           'to_country',
                           'from_state',
                           'to_state']

    @staticmethod
    def _m2m_field_name(name):
        return "%s_ids" % name

    def _map_domain(self, cr, uid, partner,
                    partner_address, company, context=None):
        """
        Replace the m2o fields by the m2m fields in the domain
        """
        domain = super(account_fiscal_position_rule, self)._map_domain(
            cr, uid, partner, partner_address, company, context=context)

        new_domain = []
        for clause in domain:
            # check type to skip the operators '|', '&'
            if (isinstance(clause, (tuple, list)) and
               clause[0] in self.m2o_replaced_fields):
                new_domain.append(
                    (self._m2m_field_name(clause[0]), clause[1], clause[2]))
            else:
                new_domain.append(clause)

        return new_domain

account_fiscal_position_rule()


class account_fiscal_position_rule_template(osv.osv):

    _inherit = "account.fiscal.position.rule.template"

    _columns = {
        'from_country_ids': fields.many2many(
            'res.country',
            rel='account_fiscal_rule_tmpl_res_country_from_rel',
            id1='rule_id', id2='country_id',
            string='Origin Countries'),
        'from_state_ids': fields.many2many(
                    'res.country.state',
                    rel='account_fiscal_rule_tmpl_state_from_rel',
                    id1='rule_id', id2='state_id',
                    string='Origin States'),
        'to_country_ids': fields.many2many(
            'res.country',
            rel='account_fiscal_rule_tmpl_res_country_to_rel',
            id1='rule_id', id2='country_id',
            string='Destination Countries'),
        'to_state_ids': fields.many2many(
                    'res.country.state',
                    rel='account_fiscal_rule_tmpl_state_to_rel',
                    id1='rule_id', id2='state_id',
                    string='Destination States'),
        }

    def init(self, cr):
        migrations = [
        {'rel_table': 'account_fiscal_rule_tmpl_res_country_to_rel',
         'from_field': 'to_country',
         'rel_field': 'country_id'},
        {'rel_table': 'account_fiscal_rule_tmpl_state_to_rel',
         'from_field': 'to_state',
         'rel_field': 'state_id'},
        {'rel_table': 'account_fiscal_rule_tmpl_res_country_from_rel',
         'from_field': 'from_country',
         'rel_field': 'country_id'},
        {'rel_table': 'account_fiscal_rule_tmpl_state_from_rel',
         'from_field': 'from_state',
         'rel_field': 'state_id'}]
        for migration in migrations:
            cr.execute("INSERT INTO %(rel_table)s "
                       "(rule_id, %(rel_field)s) "
                       "(SELECT id, %(from_field)s FROM "
                       " account_fiscal_position_rule_template "
                       "WHERE %(from_field)s IS NOT NULL "
                       " AND (id, %(from_field)s) NOT IN "
                       " (SELECT rule_id, %(rel_field)s "
                       "  FROM %(rel_table)s))" % migration)

            cr.execute("UPDATE account_fiscal_position_rule_template "
                       "SET %(from_field)s = NULL" % migration)


account_fiscal_position_rule_template()


class wizard_account_fiscal_position_rule(osv.osv_memory):

    _inherit = 'wizard.account.fiscal.position.rule'

    def _template_vals(self, cr, uid, template, company_id,
                       fiscal_position_ids, context=None):
        vals = super(wizard_account_fiscal_position_rule, self)._template_vals(
            cr, uid, template, company_id, fiscal_position_ids, context=context
        )

        for field in account_fiscal_position_rule.m2o_replaced_fields:
            field_name = "%s_ids" % field
            field_ids = [item.id for item in template[field_name]]
            vals[field_name] = [(6, 0, field_ids)]

        return vals

wizard_account_fiscal_position_rule()
