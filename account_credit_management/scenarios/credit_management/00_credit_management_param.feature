###############################################################################
#
#    OERPScenario, OpenERP Functional Tests
#    Copyright 2009 Camptocamp SA
#
##############################################################################
##############################################################################
# Branch      # Module       # Processes     # System
@credit_management_module   @credit_management_param

Feature: In order to validate account voucher behavious as an admin user I prepare data
  @credit_management_addon_install
  Scenario: Install module
    Given I need a "ir.module.module" with name: account_voucher
    And having:
      |name     | value |
      | demo    | 0     |

    Given I do not want all demo data to be loaded on install
    And I install the required modules with dependencies:
      | name                            |
      | account_credit_management       |
    Then my modules should have been installed and models reloaded