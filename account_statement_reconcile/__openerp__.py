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

{'name': "Auto reconcile statements",
 'version': '1.0',
 'author': 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Finance',
 'complexity': 'normal', #easy, normal, expert
 'depends': ['base_transaction_id'],
 'description': """
 This module allows you auto reconcile entries with payment. It is
 mostly use in E-Commerce, but could also be useful in other cases. You can choose which account 
 you want to reconcile, which partner or which invoice.
 
 The automatic reconciliation features match, if available, a transaction ID propagated from the Sale Order to 
 match transaction. If not present, it will look for the SO Name in the Origin or description of the move line.
 
 Basicaly, this module will match account move line with a matching reference on a same account. It will make
 a partial reconciliation if more than one move has the same reference (like 3x payments). Once all payment will 
 be there, it will make a full reconciliation. You can choose a write-off amount as well.
 
 """,
 'website': 'http://www.camptocamp.com',
 'init_xml': [],
 'update_xml': [
     'wizard/statement_auto_reconcile_view.xml',
 ],
 'demo_xml': [],
 'test': [],
 'installable': True,
 'images': [],
 'auto_install': False,
 'license': 'AGPL-3',
 'active': False,
}
