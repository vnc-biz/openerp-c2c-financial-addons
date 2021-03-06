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
    'name': 'Fiscal Position Rules Multi Selection',
    'version': '1.0',
    'category': 'Generic Modules',
    "author" : "Camptocamp",
    'license': 'AGPL-3',
    'description': """
Replaces the selection fields for countries and states
by multi-selection fields
on the module account fiscal position rules.


It allows to create rules from and to multiple countries
instead of one only actually.
For instance :
 - From France
 - To each country in EU
Will apply the same Fiscal Position

""",
    'images': [],
    "website" : "http://www.camptocamp.com",
    'depends': ['account_fiscal_position_rule'],
    'init_xml': [],
    'update_xml': ['fiscal_rules_view.xml', ],
    'demo_xml': [],
    'installable': False,
    'auto_install': False,
}
