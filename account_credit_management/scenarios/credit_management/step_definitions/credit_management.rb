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
