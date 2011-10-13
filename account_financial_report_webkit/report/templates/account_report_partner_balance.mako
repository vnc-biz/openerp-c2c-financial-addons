<!DOCTYPE html SYSTEM "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
    <head>
        <style type="text/css">
            ${css}

            .list_table .act_as_row {
                margin-top: 10px;
                margin-bottom: 10px;
                font-size:10px;
            }

            .account_line {
                font-weight: bold;
                font-size: 15px;
                background-color:#F0F0F0;
            }
            
            .account_line .act_as_cell {
                height: 30px;
                vertical-align: bottom;
            }

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
                <div class="act_as_cell">${_('Initial Balance')}</div>
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
                <div class="act_as_cell">${ _('Yes') if initial_balance else _('No') }</div>
            </div>
        </div>

        %for index, params in enumerate(comp_params):
            <div class="act_as_table data_table">
                <div class="act_as_row">
                    <div class="act_as_cell">${_('Comparison %s') % (index + 1,)} (${"C%s" % (index + 1,)})</div>
                    <div class="act_as_cell">
                        %if params['comparison_filter'] == 'filter_date':
                            ${_('Dates : ')}&nbsp;${formatLang(params['start'], date=True) }&nbsp;-&nbsp;${formatLang(params['stop'], date=True) }
                        %elif params['comparison_filter'] == 'filter_period':
                            ${_('Periods : ')}&nbsp;${params['start'].name}&nbsp;-&nbsp;${params['stop'].name}
                        %else:
                            ${_('Fiscal Year : ')}&nbsp;${params['fiscalyear'].name}
                        %endif
                    </div>
                    <div class="act_as_cell">${_('Initial Balance:')} ${ _('Yes') if params['initial_balance'] else _('No') }</div>
                </div>
            </div>
        %endfor


        %for partner_balance_data in objects:
            <%
            current = partner_balance_data['current']
            current_account = current['account']
            current_partner_amounts = current.get('partners_amounts', {})
            partners_order = partner_balance_data['partners_order']
            comparisons = partner_balance_data['comparisons']
            %>
            <div class="act_as_table list_table" style="margin-top: 20px;">

                <div class="act_as_thead">
                    <div class="act_as_row labels">
                        ## code
                        <div class="act_as_cell first_column" style="width: 20px;">${_('Code / Ref')}</div>
                        ## account name
                        <div class="act_as_cell" style="width: 80px;">${_('Account / Partner Name')}</div>
                        %if comparison_mode == 'no_comparison':
                            %if initial_balance:
                                ## initial balance
                                <div class="act_as_cell amount" style="width: 30px;">${_('Initial Balance')}</div>
                            %endif
                            ## debit
                            <div class="act_as_cell amount" style="width: 30px;">${_('Debit')}</div>
                            ## credit
                            <div class="act_as_cell amount" style="width: 30px;">${_('Credit')}</div>
                        %endif
                        ## balance
                        <div class="act_as_cell amount" style="width: 30px;">
                        %if comparison_mode == 'no_comparison' or not fiscalyear:
                            ${_('Balance')}
                        %else:
                            ${_('Balance %s') % (fiscalyear.name,)}
                        %endif
                        </div>
                        %if comparison_mode in ('single', 'multiple'):
                            %for index in range(nb_comparison):
                                <div class="act_as_cell amount" style="width: 30px;">
                                    %if comp_params[index]['comparison_filter'] == 'filter_year' and comp_params[index].get('fiscalyear', False):
                                        ${_('Balance %s') % (comp_params[index]['fiscalyear'].name,)}
                                    %else:
                                        ${_('Balance C%s') % (index + 1,)}
                                    %endif
                                </div>
                                %if comparison_mode == 'single':  ## no diff in multiple comparisons because it shows too data
                                    <div class="act_as_cell amount" style="width: 30px;">${_('Difference')}</div>
                                    <div class="act_as_cell amount" style="width: 30px;">${_('% Difference')}</div>
                                %endif
                            %endfor
                        %endif
                    </div>
                </div>

                <div class="act_as_tbody">

                    <div class="act_as_row lines account_line">
                        ## code
                        <div class="act_as_cell first_column">${current_account['code']}</div>
                        ## account name
                        <div class="act_as_cell">${current_account['name']}</div>
                        %if comparison_mode == 'no_comparison':
                            %if initial_balance:
                                ## opening balance
                                <div class="act_as_cell amount">${current_account['init_balance'] | amount}</div>
                            %endif
                            ## debit
                            <div class="act_as_cell amount">${current_account['debit'] | amount}</div>
                            ## credit
                            <div class="act_as_cell amount">${current_account['credit'] and current_account['credit'] * -1 or 0.0 | amount}</div>
                        %endif
                        ## balance
                        <div class="act_as_cell amount">${current_account['balance'] | amount}</div>

                        %if comparison_mode in ('single', 'multiple'):
                            %for comp in partner_balance_data['comparisons']:
                                <%
                                comp_account = comp['account']
                                %>
                                <div class="act_as_cell amount">${comp_account['balance'] | amount}</div>
                                %if comparison_mode == 'single':  ## no diff in multiple comparisons because it shows too data
                                    <div class="act_as_cell amount">${comp_account['diff'] | amount}</div>
                                    <div class="act_as_cell amount">
                                    %if comp_account['percent_diff'] is False:
                                     ${ '-' }
                                    %else:
                                       ${comp_account['percent_diff'] | amount} &#37;
                                    %endif
                                    </div>
                                %endif
                            %endfor
                        %endif
                    </div>
                
                    %for (partner_code_name, partner_id, partner_ref, partner_name) in partners_order:
                        <%
                        current = partner_balance_data['current']
                        current_account = current['account']
                        partner = current_partner_amounts.get(partner_id)
                        %>
                        <div class="act_as_row lines">
                            <div class="act_as_cell first_column">${partner_ref if partner_ref else ''}</div>
                            <div class="act_as_cell">${partner_name if partner_name else _('Unallocated') }</div>
                            %if comparison_mode == 'no_comparison':
                                %if initial_balance:
                                    <div class="act_as_cell amount">${partner['init_balance'] | amount}</div>
                                %endif
                                <div class="act_as_cell amount">${partner['debit'] if partner else 0.0 | amount}</div>
                                <div class="act_as_cell amount">${(partner['credit'] and partner['credit'] * -1 or 0.0) if partner else 0.0 | amount}</div>
                            %endif
                            <div class="act_as_cell amount">${partner['balance'] if partner else 0.0 | amount}</div>

                            %if comparison_mode in ('single', 'multiple'):
                                %for comp in partner_balance_data['comparisons']:
                                    <%
                                    comp_partners = comp['partners_amounts']
                                    balance = diff = percent_diff = 0
                                    if comp_partners.get(partner_id):
                                        balance = comp_partners[partner_id]['balance']
                                        diff = comp_partners[partner_id]['diff']
                                        percent_diff = comp_partners[partner_id]['percent_diff']
                                    %>
                                    <div class="act_as_cell amount">${balance | amount}</div>
                                    %if comparison_mode == 'single':  ## no diff in multiple comparisons because it shows too data
                                        <div class="act_as_cell amount">${diff | amount}</div>
                                        <div class="act_as_cell amount">
                                        %if percent_diff is False:
                                         ${ '-' }
                                        %else:
                                           ${percent_diff | amount} &#37;
                                        %endif
                                        </div>
                                    %endif
                                %endfor
                            %endif
                        </div>
                    %endfor

                </div>
            </div>

        %endfor

    </body>
</html>
