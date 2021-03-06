# -*- encoding: utf-8 -*-
#
#  c2c_scan_bvr
#
#  Created by Nicolas Bessi and Vincent Renaville
#
#  Copyright (c) 2012 CamptoCamp. All rights reserved.
##############################################################################
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
{
        "name" : "Account Payment improvement",
        "description" : """In case of a payment order
        set to pay directly , when the payment will pass to stade done, it will set payment line date to the current date
        """,
        "version" : "1.0",
        "author" : "Camptocamp",
        "category" : "Generic Modules/Others",
        "website": "http://www.camptocamp.com",
        "depends" : [
                        "account_payment"
                    ],
        "init_xml" : [],
        "update_xml" : [
                        'account_payment_view.xml'
                        ],
        "active": False,
        "installable": True
}
