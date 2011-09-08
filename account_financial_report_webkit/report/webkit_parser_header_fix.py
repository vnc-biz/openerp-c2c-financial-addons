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
import os
import subprocess
import tempfile
import time

from osv.osv import except_osv
from report_webkit import webkit_report


# Class used only as a workaround to bug :
# http://code.google.com/p/wkhtmltopdf/issues/detail?id=656

# html headers and footers do not work on big files (hundreds of pages) so we replace them by
# text headers and footers passed as arguments to wkhtmltopdf
# this class has to be removed once the bug is fixed

# in your report class, to print headers and footers as text, you have to add them in the localcontext with a key 'additional_args'
# for instance :
#        header_report_name = _('PARTNER LEDGER')
#        footer_date_time = self.formatLang(str(datetime.today()), date_time=True)
#        self.localcontext.update({
#            'additional_args': [
#                ('--header-font-name', 'Helvetica'),
#                ('--footer-font-name', 'Helvetica'),
#                ('--header-font-size', '10'),
#                ('--footer-font-size', '7'),
#                ('--header-left', header_report_name),
#                ('--footer-left', footer_date_time),
#                ('--footer-right', ' '.join((_('Page'), '[page]', _('of'), '[topage]'))),
#                ('--footer-line',),
#            ],
#        })

class HeaderFooterTextWebKitParser(webkit_report.WebKitParser):

    def generate_pdf(self, comm_path, report_xml, header, footer, html_list, webkit_header=False):
        """Call webkit in order to generate pdf"""
        if not webkit_header:
            webkit_header = report_xml.webkit_header
        tmp_dir = tempfile.gettempdir()
        out = report_xml.name+str(time.time())+'.pdf'
        out = os.path.join(tmp_dir, out.replace(' ',''))
        files = []
        file_to_del = []
        if comm_path:
            command = [comm_path]
        else:
            command = ['wkhtmltopdf']

        command.append('--quiet')
        # default to UTF-8 encoding.  Use <meta charset="latin-1"> to override.
        command.extend(['--encoding', 'utf-8'])

        if webkit_header.margin_top :
            command.extend(['--margin-top', str(webkit_header.margin_top).replace(',', '.')])
        if webkit_header.margin_bottom :
            command.extend(['--margin-bottom', str(webkit_header.margin_bottom).replace(',', '.')])
        if webkit_header.margin_left :
            command.extend(['--margin-left', str(webkit_header.margin_left).replace(',', '.')])
        if webkit_header.margin_right :
            command.extend(['--margin-right', str(webkit_header.margin_right).replace(',', '.')])
        if webkit_header.orientation :
            command.extend(['--orientation', str(webkit_header.orientation).replace(',', '.')])
        if webkit_header.format :
            command.extend(['--page-size', str(webkit_header.format).replace(',', '.')])

        if self.parser_instance.localcontext.get('additional_args', False):
            for arg in self.parser_instance.localcontext['additional_args']:
                command.extend(arg)

        count = 0
        for html in html_list :
            html_file = file(os.path.join(tmp_dir, str(time.time()) + str(count) +'.body.html'), 'w')
            count += 1
            html_file.write(html)
            html_file.close()
            file_to_del.append(html_file.name)
            command.append(html_file.name)
        command.append(out)
        generate_command = ' '.join(command)
        try:
            status = subprocess.call(command, stderr=subprocess.PIPE) # ignore stderr
            if status :
                raise except_osv(
                                _('Webkit raise an error' ),
                                status
                            )
        except Exception:
            for f_to_del in file_to_del :
                os.unlink(f_to_del)

        pdf = file(out, 'rb').read()
        for f_to_del in file_to_del :
            os.unlink(f_to_del)

        os.unlink(out)
        return pdf
