# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Joel Grand-Guillaume
#    Copyright 2011-2012 Camptocamp SA
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

{'name': "Credit card institue like statement import",
 'version': '1.0',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Finance',
 'complexity': 'normal', #easy, normal, expert
 'depends': ['base_transaction_id','account_statement_ext'],
 'description': """
 The goal of this module is to help dealing with huge volume of reconciliation through
 payment offices like Paypal, Lazer, Visa, Amazon and so on. It's mostly used for
 E-commerce.
 
 Features:
 
 1) This module adds a new view on bank statement called 'Treasury Statement' that allow you 
 to import your bank transactions given by those payment offices. It provide a standard
 .csv or .xls file (you'll find it in the 'data' folder) that you can easily import. We take care
 of:
  - Account commission and partner relation
  - Can force an account for the reconciliation
 
 2) Adds a report on bank statement that can be used for Checks
 
 3) When an error occurs in a bank statement, it will go through all line anyway and summarize 
 all the erronous line in a same popup instead of raising and crashing on every step.
 
 """,
 'website': 'http://www.camptocamp.com',
 'init_xml': [],
 'update_xml': [
     'statement_view.xml',
     'wizard/import_statement_view.xml',
     'report/bank_statement_webkit_header.xml',
     'report.xml',
 ],
 'demo_xml': [],
 'test': [],
 'installable': True,
 'images': [],
 'auto_install': False,
 'license': 'AGPL-3',
 'active': False,
}
