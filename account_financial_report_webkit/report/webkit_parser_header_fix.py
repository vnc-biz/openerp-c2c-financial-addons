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
import netsvc
import pooler
import tools
import addons

from mako.template import Template
from mako import exceptions
from osv.osv import except_osv
from tools.translate import _
from report_webkit import webkit_report
from report_webkit.webkit_report import mako_template
from report_webkit.report_helper import WebKitHelper


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

    # override needed to keep the attachments' storing procedure
    def create_single_pdf(self, cursor, uid, ids, data, report_xml, context=None):
        """generate the PDF"""

        if context is None:
            context={}

        if report_xml.report_type != 'webkit':
            return super(HeaderFooterTextWebKitParser,self).create_single_pdf(cursor, uid, ids, data, report_xml, context=context)

        self.parser_instance = self.parser(
                                            cursor,
                                            uid,
                                            self.name2,
                                            context=context
                                        )

        self.pool = pooler.get_pool(cursor.dbname)
        objs = self.getObjects(cursor, uid, ids, context)
        self.parser_instance.set_context(objs, data, ids, report_xml.report_type)

        template =  False

        if report_xml.report_file :
            path = addons.get_module_resource(report_xml.report_file)
            if path and os.path.exists(path) :
                template = file(path).read()
        if not template and report_xml.report_webkit_data :
            template =  report_xml.report_webkit_data
        if not template :
            import pdb; pdb.set_trace()
            raise except_osv(_('Error!'), _('Webkit Report template not found !'))
        header = report_xml.webkit_header.html
        footer = report_xml.webkit_header.footer_html
        if not header and report_xml.header:
          raise except_osv(
                _('No header defined for this Webkit report!'),
                _('Please set a header in company settings')
            )
        if not report_xml.header :
            #I know it could be cleaner ...
            header = u"""
<html>
    <head>
        <meta content="text/html; charset=UTF-8" http-equiv="content-type"/>
        <style type="text/css">
            ${css}
        </style>
        <script>
        function subst() {
           var vars={};
           var x=document.location.search.substring(1).split('&');
           for(var i in x) {var z=x[i].split('=',2);vars[z[0]] = unescape(z[1]);}
           var x=['frompage','topage','page','webpage','section','subsection','subsubsection'];
           for(var i in x) {
             var y = document.getElementsByClassName(x[i]);
             for(var j=0; j<y.length; ++j) y[j].textContent = vars[x[i]];
           }
         }
        </script>
    </head>
<body style="border:0; margin: 0;" onload="subst()">
</body>
</html>"""
        css = report_xml.webkit_header.css
        if not css :
            css = ''
        user = self.pool.get('res.users').browse(cursor, uid, uid)
        company= user.company_id


        #default_filters=['unicode', 'entity'] can be used to set global filter
        body_mako_tpl = mako_template(template)
        helper = WebKitHelper(cursor, uid, report_xml.id, context)
        self.parser_instance.localcontext.update({'setLang':self.setLang})
        self.parser_instance.localcontext.update({'formatLang':self.formatLang})
        try :
            html = body_mako_tpl.render(     helper=helper,
                                             css=css,
                                             _=self.translate_call,
                                             **self.parser_instance.localcontext
                                        )
        except Exception, e:
            msg = exceptions.text_error_template().render()
            netsvc.Logger().notifyChannel('Webkit render', netsvc.LOG_ERROR, msg)
            raise except_osv(_('Webkit render'), msg)
        head_mako_tpl = mako_template(header)
#        try :
#            head = head_mako_tpl.render(helper=helper,
#                                        css=css,
#                                        _=self.translate_call,
#                                        _debug=False,
#                                        **self.parser_instance.localcontext)
#        except Exception, e:
#            raise except_osv(_('Webkit render'),
#                exceptions.text_error_template().render())


        # NO html footer and header because we write them as text with wkhtmltopdf
        foot = False
        head = False
#        if footer :
#            foot_mako_tpl = mako_template(footer)
#            try :
#                foot = foot_mako_tpl.render(helper=helper,
#                                            css=css,
#                                            _=self.translate_call,
#                                            **self.parser_instance.localcontext)
#            except:
#                msg = exceptions.text_error_template().render()
#                netsvc.Logger().notifyChannel('Webkit render', netsvc.LOG_ERROR, msg)
#                raise except_osv(_('Webkit render'), msg)
        if report_xml.webkit_debug :
            try :
                deb = head_mako_tpl.render(helper=helper,
                                           css=css,
                                           _debug=tools.ustr(html),
                                           _=self.translate_call,
                                           **self.parser_instance.localcontext)
            except Exception, e:
                msg = exceptions.text_error_template().render()
                netsvc.Logger().notifyChannel('Webkit render', netsvc.LOG_ERROR, msg)
                raise except_osv(_('Webkit render'), msg)
            return (deb, 'html')
        bin = self.get_lib(cursor, uid, company.id)

        pdf = self.generate_pdf(bin, report_xml, head, foot, [html])
        return (pdf, 'pdf')
