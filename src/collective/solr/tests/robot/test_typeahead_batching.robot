# ============================================================================
# EXAMPLE ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s collective.solr -t test_example.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src collective.solr.testing.COLLECTIVE_SOLR_ACCEPTANCE_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot src/collective/solr/tests/robot/test_example.robot
#
# See the http://docs.plone.org for further details (search for robot
# framework).
#
# ============================================================================

*** Settings ***

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers

*** Keywords ***

# --- Given ------------------------------------------------------------------

a solr typeahead page
  Set Selenium Speed  .1 seconds
  Go To  ${PLONE_URL}/solr-typeahead
  Wait until page contains element  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]
  Element should contain  id=search-results-number  0

# --- WHEN -------------------------------------------------------------------

I enter part of query
  Input Text  SearchableText  Welcom

# --- THEN -------------------------------------------------------------------

I see autocomplete suggestion
  Wait until page contains element  css=div.tt-suggestion.tt-selectable
  Element text should be  css=div.tt-suggestion.tt-selectable  Welcome to Plone

# --- WHEN -------------------------------------------------------------------

I press submit button
  Click element  id=solr-submit

# --- THEN -------------------------------------------------------------------

I see results by short query
  Location should be  ${PLONE_URL}/solr-typeahead
  Wait until page contains element  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]
  Textfield value should be  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]  Welcom
  Wait until page contains element  css=dt.contenttype-document

  Element should contain  id=search-results-number  23
  Element should contain  css=span.sugg  welcome

  Page should contain  Next 10 items
  Page should contain  [1]
  Page should contain element  xpath=//a[@class="solr-batching" and contains(text(),'2')]
  Page should contain element  xpath=//a[@class="solr-batching" and contains(text(),'3')]
  Xpath Should Match X Times  //dt[@class="contenttype-document"]  10

# --- WHEN -------------------------------------------------------------------

I press on suggestion text
  Click element  css=span.suggestion

# --- THEN -------------------------------------------------------------------

I see suggestion in search field
  Textfield value should be  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]  welcome

# --- WHEN -------------------------------------------------------------------

I click on next 10 items button
  Click element  xpath=//a[contains(text(), 'Next 10 items')]

# --- THEN -------------------------------------------------------------------

I see second page with elements
  Page should contain  Next 10 items
  Page should contain  Previous 10 items
  Page should contain  [2]
  Page should contain element  xpath=//a[@class="solr-batching" and contains(text(),'1')]
  Page should contain element  xpath=//a[@class="solr-batching" and contains(text(),'3')]
  Textfield value should be  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]  welcome

  Xpath Should Match X Times  //dt[@class="contenttype-document"]  10

# --- WHEN -------------------------------------------------------------------

I click on previous 10 items button
  Click element  xpath=//a[contains(text(), 'Previous 10 items')]

# --- THEN -------------------------------------------------------------------

I see first page with elements
  Page should contain  Next 10 items
  Page should not contain  Previous 10 items
  Page should contain  [1]
  Page should contain element  xpath=//a[@class="solr-batching" and contains(text(),'2')]
  Page should contain element  xpath=//a[@class="solr-batching" and contains(text(),'3')]
  Textfield value should be  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]  welcome

  Xpath Should Match X Times  //dt[@class="contenttype-document"]  10

# --- WHEN -------------------------------------------------------------------

I click on the last page button
  Click element  xpath=//a[@class="solr-batching" and contains(text(),'3')]

# --- THEN -------------------------------------------------------------------

I see third (last) page with elements
  Page should not contain  Next 10 items
  Page should contain  Previous 10 items
  Page should contain  [3]
  Page should contain element  xpath=//a[@class="solr-batching" and contains(text(),'1')]
  Page should contain element  xpath=//a[@class="solr-batching" and contains(text(),'2')]
  Textfield value should be  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]  welcome

  Xpath Should Match X Times  //dt[@class="contenttype-document"]  3

# --- THEN -------------------------------------------------------------------

I can check results finally
  Xpath Should Match X Times  //a[@class="state-None" and contains(text(), 'Welcome to Plone')]  3
  Xpath Should Match X Times  //a[contains(text(), 'user2')]  3

*** Test Cases ***

Scenario: As user I want to use solr typeahead viewlet to search for something and select autocomplete suggestion
  [Documentation]  Example of a BDD-style (Behavior-driven development) test.
  Given a solr typeahead page
    When I enter part of query
    Then I see autocomplete suggestion
    When I press submit button
    Then I see results by short query
    When I press on suggestion text
    Then I see suggestion in search field
    When I click on next 10 items button
    Then I see second page with elements
    When I click on previous 10 items button
    Then I see first page with elements
    When I click on the last page button
    Then I see third (last) page with elements
    Then I can check results finally
