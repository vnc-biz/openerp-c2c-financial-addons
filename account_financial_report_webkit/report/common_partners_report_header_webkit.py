# -*- encoding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    SQL inspired from OpenERP original code
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
#TODO split file
from common_report_header_webkit import CommonReportHeaderWebkit
from tools.translate import _

class CommonPartnersReportHeaderWebkit(CommonReportHeaderWebkit):
    """Define common helper for financial report"""
    ####################Partner specific helper ##########################    
    def get_patner_ids_from_account_move_lines(self, line_ids):
       """We get the partner linked to all current accounts that are used.
          We also use ensure that partner are ordered bay name"""
       base_dict = {}
       if not isinstance(account_ids, list):
           account_ids = [account_ids]
       sql = ("SELECT DISTINCT partner_id from account_move_line where account_id in %S"
              " AND partner_id IS NOT NULL")
       self.cursor.execute(sql, (tuple(account_ids),))
       res = cr.fetchall()
       if not res:
           return base_dict
       for acc_ids in account_ids:
           base_dict
