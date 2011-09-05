<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style type="text/css">
            ${css}
        </style>
    </head>
    <body>
        <%!
        def amount(text):
            return text.replace('-', '&#8209;')  # replace by a non-breaking hyphen (it will not word-wrap between hyphen and numbers)
        %>

        <%setLang(user.address_id and user.address_id.partner_id.lang and user.address_id.partner_id.lang or 'en_US')%>

        <div class="act_as_table data_table">
            <div class="act_as_row">
                <div class="act_as_cell"><b >${_('Fiscal Year:')}</b> ${ fiscalyear.name if fiscalyear else '' }</div>
            </div>
            <div class="act_as_row">
                <div class="act_as_cell"><b>${_('Period From:')}</b> ${ start_period.name if start_period else u'' }</div>
                <div class="act_as_cell"><b>${_('to:')}</b> ${ stop_period.name if stop_period else u'' }</div>
                <div class="act_as_cell"><b>${_('Displayed Account:')}</b> ${ display_partner_account(data) }</div>
            </div>
            <div class="act_as_row">
                <div class="act_as_cell"><b>${_('Date From:')}</b> ${ formatLang(start_date, date=True) if start_date else '' }</div>
                <div class="act_as_cell"><b>${_('to:')}</b> ${ formatLang(stop_date, date=True) if stop_date else '' }</div>
                <div class="act_as_cell"><b>${_('Target Move:')}</b> ${ display_target_move(data) }</div>
            </div>
        </div>
        
        <%setLang(user.address_id and user.address_id.partner_id.lang and user.address_id.partner_id.lang or 'en_US')%>
    
        %for account in objects:
            %if account.ledger_lines or account.init_balance:
                <%
                  cumul_balance =  0.0
                  cumul_balance_curr = 0.0
                %>

                <div class="account_title bg" style="width: 1080px; margin-top: 10px;">${account.code} - ${account.name}</div>
                
                %for partner_name, p_id in account.partners_order:
                <%
                  part_cumul_balance =  0.0
                  part_cumul_balance_curr = 0.0 
                %>
                <div class="act_as_table list_table" style="margin-top: 5px;">
                    <div class="act_as_caption account_title" style="padding-left:30px">
                        ${partner_name}
                    </div>
                    <div class="act_as_thead">
                        <div class="act_as_row labels">
                            ## date
                            <div class="act_as_cell first_column" style="width: 55px;">${_('Date')}</div>
                            ## period
                            <div class="act_as_cell" style="width: 50px;">${_('Period')}</div>
                            ## move
                            <div class="act_as_cell" style="width: 110px;">${_('Move')}</div>
                            ## journal
                            <div class="act_as_cell" style="width: 50px;">${_('Journal')}</div>
                            ## partner
                            <div class="act_as_cell" style="width: 120px;">${_('Partner')}</div>
                            ## ref
                            <div class="act_as_cell" style="width: 110px;">${_('Ref')}</div>
                            ## label
                            <div class="act_as_cell" style="width: 220px;">${_('Label')}</div>
                            ## reconcile
                            <div class="act_as_cell" style="width: 50px;">${_('Reconcile')}</div>
                            ## balance
                            <div class="act_as_cell amount" style="width: 70px;">${_('Balance')}</div>
                            ## balance cumulated
                            <div class="act_as_cell amount" style="width: 70px;">${_('Cumul. Bal.')}</div>
                            %if amount_currency(data):
                                ## curency code
                                <div class="act_as_cell amount" style="width: 20px;">${_('Curr.')}</div>
                                ## currency balance
                                <div class="act_as_cell amount" style="width: 70px;">${_('Curr. Balance')}</div>
                                ## currency balance cumulated
                                <div class="act_as_cell amount" style="width: 70px;">${_('Curr. Cumul. Bal')}</div>
                            %endif
                        </div>
                    </div>
                    <div class="act_as_tbody">
                          %if initial_balance(data) and cumul_balance:
                            <%
                              part_cumul_balance = account.init_balance.get(p_id, {}).get('init_balance') or 0.0
                              part_cumul_balance_curr = account.init_balance.get(p_id, {}).get('init_balance_currency') or 0.0
                            %>
                            <div class="act_as_row initial_balance">
                              ## date
                              <div class="act_as_cell first_column"></div>
                              ## period
                              <div class="act_as_cell"></div>
                              ## move
                              <div class="act_as_cell"></div>
                              ## journal
                              <div class="act_as_cell"></div>
                              ## partner
                              <div class="act_as_cell"></div>
                              ## ref
                              <div class="act_as_cell"></div>
                              ## label
                              <div class="act_as_cell" >${_('Balance brought forward')}</div>
                              ## reconcile
                              <div class="act_as_cell"></div>
                              ## balance
                              <div class="act_as_cell amount">${formatLang(cumul_balance) | amount }</div>
                              ## balance cumulated
                              <div class="act_as_cell amount">${formatLang(cumul_balance) | amount }</div>
                             %if amount_currency(data):
                                  ## curency code
                                  <div class="act_as_cell"></div>
                                  ## currency balance
                                  <div class="act_as_cell amount">${formatLang(cumul_balance_curr) | amount }</div>
                                  %if account.currency_id:
                                      ## currency balance cumulated
                                      <div class="act_as_cell amount">${formatLang(cumul_balance_curr) | amount }</div>
                                  %else:
                                    <div class="act_as_cell amount">${formatLang(0.0) | amount }</div>
                                  %endif
                             %endif

                          </div>
                          %endif

                        %for line in account.ledger_lines.get(p_id, []):
                            <div class="act_as_row lines">
                              ## date
                              <div class="act_as_cell first_column">${formatLang(line.get('ldate') or '', date=True)}</div>
                              ## period
                              <div class="act_as_cell">${line.get('period_code') or ''}</div>
                              ## move
                              <div class="act_as_cell">${line.get('move_name') or ''}</div>
                              ## journal
                              <div class="act_as_cell">${line.get('jcode') or ''}</div>
                              ## partner
                              <div class="act_as_cell">${line.get('partner_name') or ''}</div>
                              ## ref
                              <div class="act_as_cell">${line.get('lref') or ''}</div>
                              ## label
                              <div class="act_as_cell">${line.get('lname') or ''}</div>
                              ## reconcile
                              <div class="act_as_cell">${line.get('rec_name') or ''}</div>
                              ## balance
                              <div class="act_as_cell amount">${formatLang(line.get('balance') or 0.0) | amount }</div>
                              ## balance cumulated
                              <% cumul_balance += line.get('balance') or 0.0 %>
                              <div class="act_as_cell amount">${formatLang(cumul_balance) | amount }</div>
                              %if amount_currency(data):
                                  ## curency code
                                  <div class="act_as_cell">${line.get('currency_code') or ''}</div>
                                  ## currency balance
                                  <div class="act_as_cell amount">${formatLang(line.get('amount_currency') or 0.0) | amount }</div>
                                  %if account.currency_id:
                                  <% cumul_balance_curr += line.get('amount_currency') or 0.0 %>
                                      ## currency balance cumulated
                                      <div class="act_as_cell amount">${formatLang(cumul_balance_curr) | amount }</div>
                                  %else:
                                      <div class="act_as_cell amount">${formatLang(0.0) | amount }</div>
                                  %endif
                              %endif
                          </div>
                        %endfor
                    </div>
                </div>
               %endfor

            %endif
        %endfor
    </body>
</html>
