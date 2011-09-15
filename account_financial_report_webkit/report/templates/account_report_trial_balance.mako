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
                <div class="act_as_cell">${_('Displayed Accounts')}</div>
                <div class="act_as_cell">${_('Target Moves')}</div>

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
                <div class="act_as_cell">
                    %if accounts(data):
                        ${', '.join([account.code for account in accounts(data)])}
                    %else:
                        ${_('All')}
                    %endif

                </div>
                <div class="act_as_cell">${ display_target_move(data) }</div>
            </div>
        </div>

        <div class="act_as_table list_table" style="margin-top: 5px;">
            <div class="act_as_thead">
                %if comparison_mode:
                    <div class="act_as_row labels">
                        ## code
                        <div class="act_as_cell first_column" style="width: 20px;"></div>
                        ## account name
                        <div class="act_as_cell" style="width: 50px;"></div>

                        <div class="act_as_cell amount" style="width: 50px; font-weight: bold;">Main Selection</div>
                        ## credit
                        <div class="act_as_cell amount" style="width: 50px;"></div>
                        ## balance
                        <div class="act_as_cell amount" style="width: 50px;"></div>
                        %if comparison_mode:
                            <div class="act_as_cell amount" style="width: 50px; font-weight: bold;">Comparison Selection</div>
                        %endif
                    </div>
                %endif
                <div class="act_as_row labels">
                    ## code
                    <div class="act_as_cell first_column" style="width: 20px;">${_('Code')}</div>
                    ## account name
                    <div class="act_as_cell" style="width: 50px;">${_('Account')}</div>
                    %if not comparison_mode:
                        %if initial_balance:
                            ## initial balance
                            <div class="act_as_cell amount" style="width: 50px;">${_('Opening Balance')}</div>
                        %endif
                        ## debit
                        <div class="act_as_cell amount" style="width: 50px;">${_('Debit')}</div>
                        ## credit
                        <div class="act_as_cell amount" style="width: 50px;">${_('Credit')}</div>
                    %endif
                    ## balance
                    <div class="act_as_cell amount" style="width: 50px;">${_('Balance')}</div>
                    %if comparison_mode:
                        <div class="act_as_cell amount" style="width: 50px;">${_('Comparison Balance')}</div>
                    %endif
                </div>
            </div>
            <div class="act_as_tbody">
                %for account_at in objects:
                    <%
                    current_account = account_at['current']
                    comparison1_account = account_at.get('comparison1', False)
                    comparison2_account = account_at.get('comparison2', False)
                    %>

                    <div class="act_as_row lines">
                        ## code
                        <div class="act_as_cell first_column">${current_account['code']}</div>
                        ## account name
                        <div class="act_as_cell" style="padding-left: ${current_account.get('level', 0) * 3}px;">${current_account['name']}</div>
                        %if not comparison_mode:
                            %if initial_balance:
                                ## opening balance
                                <div class="act_as_cell amount">${current_account['init_balance'] | amount}</div>
                            %endif
                            ## debit
                            <div class="act_as_cell amount">${current_account['debit'] | amount}</div>
                            ## credit
                            <div class="act_as_cell amount">${current_account['credit'] | amount}</div>
                        %endif
                        ## balance
                        <div class="act_as_cell amount">${current_account['balance'] | amount}</div>

                        %if comparison_mode:
                            <div class="act_as_cell amount">${comparison1_account['balance'] | amount}</div>
                            <div class="act_as_cell amount">${comparison1_account['diff'] | amount}</div>
                            <div class="act_as_cell amount">${comparison1_account['percent_diff'] | amount} &#37;</div>

                            <div class="act_as_cell amount">${comparison2_account['balance'] | amount}</div>
                            <div class="act_as_cell amount">${comparison2_account['diff'] | amount}</div>
                            <div class="act_as_cell amount">${comparison2_account['percent_diff'] | amount} &#37;</div>
                        %endif
                    </div>
                %endfor
            </div>
        </div>
    </body>
</html>
