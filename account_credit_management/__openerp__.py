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
{'name' : 'Account Credit Management',
 'version' : '0.1',
 'author' : 'Camptocamp',
 'maintainer': 'Camptocamp',
 'category': 'Finance',
 'complexity': "normal",  # easy, normal, expert
 'depends' : ['base', 'account', 'email_template', 'report_webkit'],
 'description': """Credit control management TODO""",
 'website': 'http://www.camptocamp.com',
 'init_xml': ["data.xml"],
 'update_xml': ["credit_management_line_view.xml",
                "credit_management_account_view.xml",
                "credit_management_partner_view.xml",
                "credit_management_profile_view.xml",
                "credit_management_run_view.xml",
                "credit_management_company_view.xml",
                "wizard/credit_management_mailer_view.xml",
                "wizard/credit_management_marker_view.xml",
                "wizard/credit_management_printer_view.xml",
                "report/report.xml",
                "security/ir.model.access.csv",],
                #"credit_management_demo.xml"],
 'demo_xml': ["credit_management_demo.xml"],
 'tests': [],
 'installable': False,
 'license': 'AGPL-3',
 'application': True}
