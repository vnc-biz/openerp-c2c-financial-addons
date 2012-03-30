# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author Nicolas Bessi. Copyright Camptocamp SA
##############################################################################

from osv import fields, osv, orm

class AccountTaxCode(osv.osv):
    _inherit = 'account.tax.code'
    _name = 'account.tax.code'
    _order = 'name'
AccountTaxCode()