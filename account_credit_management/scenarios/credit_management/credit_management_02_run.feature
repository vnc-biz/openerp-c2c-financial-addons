###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2012 Camptocamp SA
#    Author Nicolas Bessi
##############################################################################

# Features Generic tags (none for all)
##############################################################################

@credit_management_module

Feature: Ensure that mail credit line generation first pass is correct


  @credit_management_first_run
  Scenario: Create run
    Given I need a "credit.management.run" with oid: credit_management.run1
    And having:
      | name |      value |
      | date | 2012-03-01 |
    Then I launch the credit run
