# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2011 Camptocamp SA (http://www.camptocamp.com)
#
# Author : Guewen Baconnier (Camptocamp)
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################


from osv import fields, osv
from lxml import etree
from tools.translate import _
from datetime import datetime

COMPARISON_LEVEL = 3

def previous_year_date(date, nb_prev=1):
    if not date:
        return False
    parsed_date = datetime.strptime(date, '%Y-%m-%d')
    previous_date = datetime(year=parsed_date.year - nb_prev,
                             month=parsed_date.month,
                             day=parsed_date.day)
    return previous_date

class AccountBalanceCommonWizard(osv.osv_memory):
    """Will launch trial balance report and pass required args"""

    _inherit = "account.common.account.report"
    _name = "account.common.balance.report"
    _description = "Common Balance Report"

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

    def _check_fiscalyear(self, cr, uid, ids, context=None):
        obj = self.read(cr, uid, ids[0], ['fiscalyear_id', 'filter'], context=context)
        if not obj['fiscalyear_id'] and obj['filter'] == 'filter_no':
            return False
        return True

    _constraints = [
        (_check_fiscalyear, 'When no Fiscal year is selected, you must choose to filter by periods or by date.', ['filter']),
    ]

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
        res = super(AccountBalanceCommonWizard, self).default_get(cr, uid, fields, context=context)
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
        res = super(AccountBalanceCommonWizard, self).view_init(cr, uid, fields_list, context=context)
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
        res = super(AccountBalanceCommonWizard, self).fields_view_get(cr, uid, view_id, view_type, context=context, toolbar=toolbar, submenu=submenu)

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
                                                    'on_change': "onchange_comp_filter(%(index)s, filter, comp%(index)s_filter, fiscalyear_id, date_from, date_to)" % {'index': index}}))
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

    def onchange_comp_filter(self, cr, uid, ids, index, main_filter='filter_no', comp_filter='filter_no', fiscalyear_id=False, start_date=False, stop_date=False, context=None):
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
            dates = {}
            if main_filter == 'filter_date':
                dates = {
                    'date_start': previous_year_date(start_date, index + 1).strftime('%Y-%m-%d'),
                    'date_stop': previous_year_date(stop_date, index + 1).strftime('%Y-%m-%d'),}
            elif last_fiscalyear_id:
                dates = fy_obj.read(cr, uid, last_fiscalyear_id, ['date_start', 'date_stop'], context=context)

            res['value'] = {fy_id_field: False, period_from_field: False, period_to_field: False, date_from_field: dates.get('date_start', False), date_to_field: dates.get('date_stop', False)}
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
        data = super(AccountBalanceCommonWizard, self).pre_print_report(cr, uid, ids, data, context)
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

AccountBalanceCommonWizard()
