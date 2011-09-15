# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Guewen Baconnier
#    Copyright Camptocamp SA 2011
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
import time

from osv import fields, osv
from lxml import etree
from tools.translate import _

COMPARISON_LEVEL = 3

class AccountTrialBalanceLedgerWizard(osv.osv_memory):
    """Will launch trial balance report and pass required args"""

    _inherit = "account.common.partner.report"
    _name = "account.report.balance.webkit"
    _description = "Trial Balance Report"

    COMPARE_SELECTION = [('filter_no', 'No Comparison'),
                         ('filter_year', 'Fiscal Year'),
                         ('filter_date', 'Date'),
                         ('filter_period', 'Periods'),]

    def _get_account_ids(self, cr, uid, context=None):
        res = False
        if context.get('active_model', False) == 'account.account' and context.get('active_ids', False):
            res = context['active_ids']
        return res

    _columns = {
        'account_ids': fields.many2many('account.account', 'wiz_account_rel',
                                        'account_id', 'wiz_id', 'Filter on accounts',
                                         help="Only selected accounts will be printed. Leave empty to print all accounts."),
    }
    _defaults = {
        'account_ids': _get_account_ids,
    }

    def default_get(self, cr, uid, fields, context=None):
        """
             To get default values for the object.

             @param self: The object pointer.
             @param cr: A database cursor
             @param uid: ID of the user currently logged in
             @param fields: List of fields for which we want default values
             @param context: A standard dictionary

             @return: A dictionary which of fields with values.

        """
        res = super(AccountTrialBalanceLedgerWizard, self).default_get(cr, uid, fields, context=context)
        for index in range(COMPARISON_LEVEL):
            res["comp%s_filter" % (index,)] = 'filter_no'
        return res

    def view_init(self, cr, uid, fields_list, context=None):
        """
         Creates view dynamically and adding fields at runtime.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param context: A standard dictionary
         @return: New arch of view with new columns.
        """
        res = super(AccountTrialBalanceLedgerWizard, self).view_init(cr, uid, fields_list, context=context)
        for index in range(COMPARISON_LEVEL):
            # create columns for each comparison page
            self._columns.update({
                "comp%s_filter" % (index,):
                    fields.selection(self.COMPARE_SELECTION,
                                     string="Compare By",
                                     required=True),
                "comp%s_fiscalyear_id" % (index,):
                    fields.many2one('account.fiscalyear', 'Fiscal year'),
                "comp%s_period_from" % (index,):
                    fields.many2one('account.period', 'Start period'),
                "comp%s_period_to" % (index,):
                    fields.many2one('account.period', 'End period'),
                "comp%s_date_from" % (index,):
                    fields.date("Start Date"),
                "comp%s_date_to" % (index,):
                    fields.date("End Date"),
            })
        return res

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(AccountTrialBalanceLedgerWizard, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)

        eview = etree.fromstring(res['arch'])
        placeholder = eview.xpath("//page[@name='placeholder']")
        if placeholder:
            placeholder = placeholder[0]
            for index in range(COMPARISON_LEVEL):
                # add fields
                res['fields']["comp%s_filter" % (index,)] = {'string': "Compare By", 'type': 'selection', 'selection': self.COMPARE_SELECTION, 'required': True}
                res['fields']["comp%s_fiscalyear_id" % (index,)] = {'string': "Fiscal Year", 'type': 'many2one', 'relation': 'account.fiscalyear'}
                res['fields']["comp%s_period_from" % (index,)] = {'string': "Start Period", 'type': 'many2one', 'relation': 'account.period'}
                res['fields']["comp%s_period_to" % (index,)] = {'string': "End Period", 'type': 'many2one', 'relation': 'account.period'}
                res['fields']["comp%s_date_from" % (index,)] = {'string': "Start Date", 'type': 'date'}
                res['fields']["comp%s_date_to" % (index,)] = {'string': "End Date", 'type': 'date'}


                page = etree.Element('page', {'name': "comp%s" % (index+1,), 'string': _("Comparison %s") % (index+1,)})
                page.append(etree.Element('field', {'name': "comp%s_filter" % (index,),
                                                    'colspan': '4', 
                                                    'on_change': "onchange_comp_filter(%(index)s, comp%(index)s_filter, fiscalyear_id)" % {'index': index}}))
                page.append(etree.Element('field', {'name': "comp%s_fiscalyear_id" % (index,),
                                                    'colspan': '4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_year')], 'readonly':[('comp%(index)s_filter','!=','filter_year')]}" % {'index': index}}))
                page.append(etree.Element('separator', {'string': _('Dates'), 'colspan':'4'}))
                page.append(etree.Element('field', {'name': "comp%s_date_from" % (index,), 'colspan':'4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_date')], 'readonly':[('comp%(index)s_filter','!=','filter_date')]}" % {'index': index}}))
                page.append(etree.Element('field', {'name': "comp%s_date_to" % (index,), 'colspan':'4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_date')], 'readonly':[('comp%(index)s_filter','!=','filter_date')]}" % {'index': index}}))
                page.append(etree.Element('separator', {'string': _('Periods'), 'colspan':'4'}))
                page.append(etree.Element('field', {'name': "comp%s_period_from" % (index,),
                                                    'colspan': '4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_period')], 'readonly':[('comp%(index)s_filter','!=','filter_period')]}" % {'index': index}}))
                page.append(etree.Element('field', {'name': "comp%s_period_to" % (index,),
                                                    'colspan': '4',
                                                    'attrs': "{'required': [('comp%(index)s_filter','=','filter_period')], 'readonly':[('comp%(index)s_filter','!=','filter_period')]}" % {'index': index}}))

                placeholder.addprevious(page)
            placeholder.getparent().remove(placeholder)
        res['arch'] = etree.tostring(eview)
        return res

    def onchange_comp_filter(self, cr, uid, ids, index, comp_filter='filter_no', fiscalyear_id=False, context=None):
        res = {}
        fy_obj = self.pool.get('account.fiscalyear')
        last_fiscalyear_id = False
        if fiscalyear_id:
            fiscalyear = fy_obj.browse(cr, uid, fiscalyear_id, context=context)
            last_fiscalyear_ids = fy_obj.search(cr, uid, [('date_stop', '<', fiscalyear.date_start)],
                                                limit=COMPARISON_LEVEL, order='date_start desc', context=context)
            if last_fiscalyear_ids:
                if len(last_fiscalyear_ids) > index:
                    last_fiscalyear_id = last_fiscalyear_ids[index]  # first element for the comparison 1, second element for the comparison 2

        fy_id_field = "comp%s_fiscalyear_id" % (index,)
        period_from_field = "comp%s_period_from" % (index,)
        period_to_field = "comp%s_period_to" % (index,)
        date_from_field = "comp%s_date_from" % (index,)
        date_to_field = "comp%s_date_to" % (index,)

        if comp_filter == 'filter_no':
            res['value'] = {fy_id_field: False, period_from_field: False, period_to_field: False, date_from_field: False ,date_to_field: False}
        if comp_filter == 'filter_year':
            res['value'] = {fy_id_field: last_fiscalyear_id, period_from_field: False, period_to_field: False, date_from_field: False ,date_to_field: False}
        if comp_filter == 'filter_date':
            # todo one or 2 years ago
            res['value'] = {fy_id_field: False, period_from_field: False, period_to_field: False, date_from_field: time.strftime('%Y-01-01'), date_to_field: time.strftime('%Y-%m-%d')}
        if comp_filter == 'filter_period' and last_fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %(fiscalyear)s
                               AND p.special = false
                               ORDER BY p.date_start ASC
                               LIMIT 1) AS period_start
                UNION
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %(fiscalyear)s
                               AND p.date_start < NOW()
                               AND p.special = false
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', {'fiscalyear': last_fiscalyear_id})
            periods =  [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = periods[0]
                end_period = periods[1]
            res['value'] = {fy_id_field: False, period_from_field: start_period, period_to_field: end_period, date_from_field: False, date_to_field: False}
        return res

    def pre_print_report(self, cr, uid, ids, data, context=None):
        data = super(AccountTrialBalanceLedgerWizard, self).pre_print_report(cr, uid, ids, data, context)
        if context is None:
            context = {}

        fields_to_read = ['account_ids',]

        # comparison fields
        for index in range(COMPARISON_LEVEL):
            fields_to_read.extend([
                "comp%s_filter" % (index,),
                "comp%s_fiscalyear_id" % (index,),
                "comp%s_period_from" % (index,),
                "comp%s_period_to" % (index,),
                "comp%s_date_from" % (index,),
                "comp%s_date_to" % (index,),
            ])

        vals = self.read(cr, uid, ids, fields_to_read,context=context)[0]
        vals['max_comparison'] = COMPARISON_LEVEL
        data['form'].update(vals)
        return data

    def _print_report(self, cursor, uid, ids, data, context=None):
        context = context or {}
        # we update form with display account value
        data = self.pre_print_report(cursor, uid, ids, data, context=context)

        return {'type': 'ir.actions.report.xml',
                'report_name': 'account.account_report_trial_balance_webkit',
                'datas': data}

AccountTrialBalanceLedgerWizard()
