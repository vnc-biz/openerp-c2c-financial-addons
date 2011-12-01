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

        <%setLang(user.context_lang)%>

        <div class="act_as_table data_table">
            <div class="act_as_row labels">
                <div class="act_as_cell">${_('Chart of Account')}</div>
                <div class="act_as_cell">${_('Fiscal Year')}</div>
                <div class="act_as_cell">
                    %if filter_form(data) == 'filter_date':
                        ${_('Dates')}
                    %else:
                        ${_('Periods')}
                    %endif
                </div>
                <div class="act_as_cell">${_('Report Date')}</div>
                <div class="act_as_cell">${_('Displayed Accounts')}</div>
                <div class="act_as_cell">${_('Target Moves')}</div>
                <div class="act_as_cell">${_('Exclude Fully Reconciled Entries')}</div>

            </div>
            <div class="act_as_row">
                <div class="act_as_cell">${ chart_account.name }</div>
                <div class="act_as_cell">${ fiscalyear.name if fiscalyear else '-' }</div>
                <div class="act_as_cell">
                    ${_('From:')}
                    %if filter_form(data) == 'filter_date':
                        ${formatLang(start_date, date=True) if start_date else u'' }
                    %else:
                        ${start_period.name if start_period else u''}
                    %endif
                    ${_('To:')}
                    %if filter_form(data) == 'filter_date':
                        ${ formatLang(stop_date, date=True) if stop_date else u'' }
                    %else:
                        ${stop_period.name if stop_period else u'' }
                    %endif
                </div>
                <div class="act_as_cell">${ formatLang(date_until, date=True) }</div>
                <div class="act_as_cell">
                    %if partner_ids:
                        ${_('Custom Filter')}
                    %else:
                        ${ display_partner_account(data) }
                    %endif
                </div>
                <div class="act_as_cell">${ display_target_move(data) }</div>
                <div class="act_as_cell">${ exclude_reconcile and _('Yes') or _('No') }</div>
            </div>
        </div>
    
        %for account in objects:
            %if account.ledger_lines or account.init_balance:
                <%
                if not account.partners_order:
                    continue
                account_balance_cumul = 0.0
                account_balance_cumul_curr = 0.0
                %>

                <div class="account_title bg" style="width: 1080px; margin-top: 20px; font-size: 12px;">${account.code} - ${account.name}</div>
                
                %for partner_name, p_id, p_ref, p_name in account.partners_order:
                <%
                  cumul_balance = 0.0
                  cumul_balance_curr = 0.0

                  part_cumul_balance = 0.0
                  part_cumul_balance_curr = 0.0 
                %>
                <div class="act_as_table list_table" style="margin-top: 5px;">
                    <div class="act_as_caption account_title">
                        ${partner_name or _('No Partner')}
                    </div>
                    <div class="act_as_thead">
                        <div class="act_as_row labels">
                            ## date
                            <div class="act_as_cell first_column" style="width: 60px;">${_('Date')}</div>
                            ## period
                            <div class="act_as_cell" style="width: 50px;">${_('Period')}</div>
                            ## move
                            <div class="act_as_cell" style="width: 80px;">${_('Entry')}</div>
                            ## journal
                            <div class="act_as_cell" style="width: 50px;">${_('Journal')}</div>
                            ## partner
                            <div class="act_as_cell" style="width: 100px;">${_('Partner')}</div>
                            ## ref
                            <div class="act_as_cell" style="width: 110px;">${_('Ref')}</div>
                            ## label
                            <div class="act_as_cell" style="width: 170px;">${_('Label')}</div>
                            ## reconcile
                            <div class="act_as_cell" style="width: 70px;">${_('Rec.')}</div>
                            ## maturity
                            <div class="act_as_cell" style="width: 60px;">${_('Due Date')}</div>
                            ## balance
                            <div class="act_as_cell amount" style="width: 75px;">${_('Balance')}</div>
                            ## balance cumulated
                            <div class="act_as_cell amount" style="width: 75px;">${_('Cumul. Bal.')}</div>
                            %if amount_currency(data):
                                ## curency code
                                <div class="act_as_cell amount sep_left" style="width: 30px; text-align: right;">${_('Curr.')}</div>
                                ## currency balance
                                <div class="act_as_cell amount" style="width: 75px;">${_('Curr. Balance')}</div>
                                ## currency balance cumulated
                                <div class="act_as_cell amount" style="width: 75px;">${_('Curr. Cumul. Bal')}</div>
                            %endif
                        </div>
                    </div>
                    <div class="act_as_tbody">
                          %if initial_balance(data) and (account.init_balance.get(p_id, {}).get('init_balance') or account.init_balance.get(p_id, {}).get('init_balance_currency')):
                            <%
                              part_cumul_balance = account.init_balance.get(p_id, {}).get('init_balance') or 0.0
                              part_cumul_balance_curr = account.init_balance.get(p_id, {}).get('init_balance_currency') or 0.0
                              balance_forward_currency = account.init_balance.get(p_id, {}).get('currency_name') or ''

                              cumul_balance += part_cumul_balance
                              cumul_balance_curr += part_cumul_balance_curr
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
                              ## maturity date
                              <div class="act_as_cell"></div>
                              ## balance
                              <div class="act_as_cell amount">${formatLang(part_cumul_balance) | amount }</div>
                              ## balance cumulated
                              <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(part_cumul_balance) | amount }</div>
                             %if amount_currency(data):
                                  ## curency code
                                  <div class="act_as_cell sep_left">${balance_forward_currency}</div>
                                  ## currency balance
                                  <div class="act_as_cell amount">${formatLang(part_cumul_balance_curr) | amount }</div>
                                  %if account.currency_id:
                                      ## currency balance cumulated
                                      <div class="act_as_cell amount">${formatLang(part_cumul_balance_curr) | amount }</div>
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
                              ## maturity date
                              <div class="act_as_cell">${formatLang(line.get('date_maturity') or '', date=True)}</div>
                              ## balance
                              <div class="act_as_cell amount">${formatLang(line.get('balance') or 0.0) | amount }</div>
                              ## balance cumulated
                              <% cumul_balance += line.get('balance') or 0.0 %>
                              <div class="act_as_cell amount" style="padding-right: 1px;">${formatLang(cumul_balance) | amount }</div>
                              %if amount_currency(data):
                                  ## curency code
                                  <div class="act_as_cell sep_left" style="text-align: right; ">${line.get('currency_code') or ''}</div>
                                  ## currency balance
                                  <div class="act_as_cell amount">${formatLang(line.get('amount_currency') or 0.0) | amount }</div>
                                  %if account.currency_id:
                                      <% cumul_balance_curr += line.get('amount_currency') or 0.0 %>
                                      ## currency balance cumulated
                                      <div class="act_as_cell amount">${formatLang(cumul_balance_curr) | amount }</div>
                                  %else:
                                      <div class="act_as_cell amount">${ u'0.0' }</div>
                                  %endif
                              %endif
                          </div>
                        %endfor
                    </div>
                </div>
                <%
                    account_balance_cumul += cumul_balance
                    account_balance_cumul_curr += cumul_balance_curr
                %>
                %endfor
                <div class="act_as_table list_table" style="margin-top:5px;">
                    <div class="act_as_row labels" style="font-weight: bold;">
                            <div class="act_as_cell first_column" style="width: 450px;">${account.code} - ${account.name}</div>
                            ## label
                            <div class="act_as_cell" style="width: 200px;">Cumulated Balance on Account</div>
                            ## reconcile
                            <div class="act_as_cell" style="width: 100px;"></div>
                            ## balance
                            <div class="act_as_cell amount" style="width: 75px;"></div>
                            ## balance cumulated
                            <div class="act_as_cell amount" style="width: 75px; padding-right: 1px;">${ formatLang(account_balance_cumul) | amount }</div>
                            %if amount_currency(data):
                                ## curency code
                                <div class="act_as_cell amount sep_left" style="width: 30px; text-align: right;">${ account.currency_id.name if account.currency_id else u'' }</div>
                                ## currency balance
                                <div class="act_as_cell amount" style="width: 75px;"></div>
                                ## currency balance cumulated
                                %if account.currency_id:
                                    <div class="act_as_cell amount" style="width: 75px;">${ formatLang(account_balance_cumul_curr) | amount }</div>
                                %else:
                                    <div class="act_as_cell amount" style="width: 75px;">${ u'0.0' }</div>
                                %endif
                            %endif
                        </div>
                    </div>
                </div>
            %endif
        %endfor
    </body>
</html>
