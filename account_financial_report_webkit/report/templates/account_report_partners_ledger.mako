<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style type="text/css">
            ${css}
        </style>
    </head>
    <body>
        <table width="1080" class="data_table" >
            <tr>
                <td width="30%"><b >${_('Fiscal Year:')}</b></td><td width="30%"></td><td width="30%"></td>
            </tr>
            <tr>
                <td><b>${_('Period From:')}</b></td><td><b>${_('to:')}</b></td><td><b>${_('Displayed Account:')}</b></td>
            </tr>
            <tr>
                <td><b>${_('Date From:')}</b></td><td><b>${_('to:')}</b></td><td><b>${_('Target Move:')}</b></td>
            </tr>
        </table>
        <br/>
        <%setLang(user.address_id and user.address_id.partner_id.lang and user.address_id.partner_id.lang or 'en_US')%>
        %for account in objects:

        %endfor
    </body>
</html>