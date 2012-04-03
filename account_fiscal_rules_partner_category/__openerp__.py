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

{
    'name': 'Fiscal Position Rules based on Partner Category',
    'version': '1.0',
    'category': 'Generic Modules',
    "author" : "Camptocamp",
    'license': 'AGPL-3',
    'description': """
Introduces a Fiscal Category on the Partners.

It can thereby be used in fiscal position rules.

Based on the module account_fiscal_position_rule which is a dependency for this module.

""",
    'images': [],
    "website" : "http://www.camptocamp.com",
    'depends': ['account_fiscal_position_rule',
                'account_fiscal_position_rule_m2m'],
    'init_xml': [],
    'update_xml': ['partner_view.xml',
                   'fiscal_rules_view.xml', ],
    'demo_xml': [],
    'installable': True,
    'auto_install': False,
}
