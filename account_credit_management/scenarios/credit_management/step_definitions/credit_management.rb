Given /^I open the credit invoice$/ do
 @found_item.should_not be_nil,
  "no invoice found"
 ['draft', 'open'].should include(@found_item.state),
  "Invoice is not draf or open"
 if @found_item.state == 'draft'
   @found_item.wkf_action('invoice_open')
 end
end

Then /^I launch the credit run$/ do
  @found_item.should_not be_nil,
  "no run found"
  @found_item.generate_credit_lines()
end

Given /^there is "(.*?)" credit lines$/ do |state|
  @credit_lines = CreditManagementLine.find_all_by_state(state)
  @credit_lines.should_not be_nil,
  "not #{state} lines found"
end

Given /^I mark all draft mail to state "(.*?)"$/ do | state |
  wiz = CreditManagementMarker.new
  wiz.name = state
  wiz.mark_all = true
  wiz.save
  wiz.mark_line
end

Then /^the draft line should be in state "(.*?)"$/ do | state |
  @credit_lines.should be_nil,
  "no line where stored"
  @credit_lines.each do |line|
    CreditManagementLine.find(line.id).state.should equal(state),
    "The line #{line.id} is not in state #{state}"

end

Given /^I mail all ready lines$/ do
  @credit_lines.should be_nil,
  "no line where stored"
  wiz = CreditManagementMailer.new
  wiz.mail_all = true
  wiz.save
  wiz.mail_lines

end

Then /^All sent lines should be linked to a mail and in mail status "(.*?)"$/ do |status|
  @credit_lines.should be_nil,
  "no line where stored"
  @credit_lines.each do |line|
    CreditManagementLine.find(line.id).mail_status.should equal(status),
    "The line #{line.id} is has no mail status #{state}"
end
