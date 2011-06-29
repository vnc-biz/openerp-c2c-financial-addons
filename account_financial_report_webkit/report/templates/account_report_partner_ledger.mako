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
          %if display_account_raw(data) == 'all' or (account.ledger_lines or account.init_balance.get('init_balance')):
              <%
              cumul_balance =  0.0
              cumul_balance_curr = 0.0 
              %>
        <span class="title">${account.code} - ${account.name}</span>
            <table class="list_table" width="1080px">
                <thead>
                    <tr> 
                        ## date
                        <td width="60px">${_('Date')}</td>
                        ## period
                        <td width="60px">${_('Period')}</td>
                        ## move
                        <td width="120px">${_('Move')}</td>
                        ## journal
                        <td width="60px">${_('Journal')}</td>
                        ## partner
                        <td width="120px">${_('Partner')}</td>
                        ## ref
                        <td width="100px">${_('Ref')}</td>
                        ## label
                        <td width="200px">${_('Label')}</td>
                        ## counterpart
                        <td width="120px">${_('Counter part')}</td>
                        ## reconcile
                        <td width="50px">${_('Reconcile')}</td>
                        ## balance
                        <td width="55px" style="word-wrap:normal; text-align:right">${_('Balance')}</td>
                        ## balance cumulated
                        <td width="55px" style="word-wrap:normal; text-align:right">${_('C. Balance')}</td>
                        %if amount_currency(data):
                        ## curency code
                        <td width="30px" style="word-wrap:normal; text-align:right">${_('Curr.')}</td>
                        ## currency balance
                        <td width="55px" style="word-wrap:normal; text-align:right">${_('Curr. Balance')}</td>
                        %if account.currency_id:
                        ## currency balance cumulated
                        <td width="55px" style="word-wrap:normal; text-align:right">${_('C. Cumul. Balance')}</td>
                        %endif
                        %endif</tr>
                </thead>
                
                <tbody>
                      %if initial_balance(data):
                        <%
                        cumul_balance = account.init_balance.get('init_balance', 0.0)
                        cumul_balance_curr = account.init_balance.get('init_balance_currency', 0.0)
                        %>
                        <tr>
                          ## date
                          <td ></td>
                          ## period
                          <td></td>
                          ## move
                          <td></td>
                          ## journal
                          <td></td>
                          ## partner
                          <td></td>
                          ## ref
                          <td></td>
                          ## label
                          <td>${_('Balance brought forward')}</td>
                          ## counterpart
                          <td></td>
                          ## reconcile
                          <td></td>
                          ## balance
                          <td style="word-wrap:normal; text-align:right">${formatLang(cumul_balance)}</td>
                          ## balance cumulated
                          <td style="word-wrap:normal; text-align:right">${formatLang(cumul_balance)}</td>
                         %if amount_currency(data):
                              ## curency code
                              <td style="word-wrap:normal; text-align:right"></td>
                              ## currency balance
                              <td style="word-wrap:normal; text-align:right">${formatLang(cumul_balance_curr)}</td>
                              %if account.currency_id:
                                  ## currency balance cumulated
                                  <td style="word-wrap:normal; text-align:right">${formatLang(cumul_balance_curr)}</td>
                              %endif
                         %endif

                      </tr>
                      %endif
                      %for line in account.ledger_lines:
                      <tr>
                          ## date
                          <td>${formatLang(line.get('ldate', False), date=True)}</td>
                          ## period
                          <td>${line.get('period_code', '')}</td>
                          ## move
                          <td>${line.get('move_name', '')}</td>
                          ## journal
                          <td>${line.get('jcode', '')}</td>
                          ## partner
                          <td>${line.get('partner_name', '')}</td>
                          ## ref
                          <td>${line.get('lref', '')}</td>
                          ## label
                          <td>${line.get('lname', '')}</td>
                          ## counterpart
                          <td>${line.get('counterparts', '')}</td>
                          ## reconcile
                          <td>${line.get('rec_name', '')}</td>
                          ## balance
                          <td style="word-wrap:normal; text-align:right">${formatLang(line.get('balance', 0.0))}</td>
                          ## balance cumulated
                          <% cumul_balance += line.get('balance', 0.0) %>
                          <td style="word-wrap:normal; text-align:right">${formatLang(cumul_balance)}</td>
                          %if amount_currency(data):
                              ## curency code
                              <td>${line.get('currency_code','')|entity}</td>
                              ## currency balance
                              <td style="word-wrap:normal; text-align:right">${formatLang(line.get('amount_currency', 0.0))}</td>
                              %if account.currency_id:
                              <% cumul_balance_curr += line.get('amount_currency', 0.0) %>
                                  ## currency balance cumulated
                                  <td style="word-wrap:normal; text-align:right">${formatLang(cumul_balance_curr)}</td>
                              %endif
                          %endif
                      </tr>
                      %endfor
                  </tbody>
              </table>
              <br/>
          %endif
        %endfor
    </body>
</html>