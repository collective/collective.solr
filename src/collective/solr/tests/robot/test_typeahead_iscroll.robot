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

a solr typeahead page with infinite scroll mode
  Go To  ${PLONE_URL}/login_form
  Wait until page contains  Login Name
  Wait until page contains  Password
  Input Text  __ac_name  admin
  Input Text  __ac_password  secret
  Click Button  Log in
  Go To  ${PLONE_URL}/@@typeahead-search-controlpanel
  Select From List By Value  id=form.results_page_mode  InfiniteScroll
  Click Element  xpath=//input[@id="form.actions.save"]
  Go To  ${PLONE_URL}/logout

  Set Selenium Speed  .5 seconds
  Go To  ${PLONE_URL}/solr-typeahead
  Wait until page contains element  xpath=//input[@id='SearchableTextIScroll' and @class="typeahead tt-input"]
  Element should contain  id=search-results-number  0

# --- WHEN -------------------------------------------------------------------

I enter part of query
  Input Text  SearchableTextIScroll  Welcom

# --- THEN -------------------------------------------------------------------

I see autocomplete suggestion
  Wait until page contains element  css=div.tt-suggestion.tt-selectable
  Element text should be  css=div.tt-suggestion.tt-selectable  Welcome to Plone

# --- WHEN -------------------------------------------------------------------

I press submit button
  Click element  id=solr-submit-iscroll

# --- THEN -------------------------------------------------------------------

I see results by short query
  Location should be  ${PLONE_URL}/solr-typeahead
  Wait until page contains element  xpath=//input[@id='SearchableTextIScroll' and @class="typeahead tt-input"]
  Textfield value should be  xpath=//input[@id='SearchableTextIScroll' and @class="typeahead tt-input"]  Welcom
  Wait until page contains element  css=dt.contenttype-document

  Element should contain  id=search-results-number  23
  Element should contain  css=span.sugg  welcome

  Xpath Should Match X Times  //dt[@class="contenttype-document"]  10
  Page should contain  Next 10 items

# --- WHEN -------------------------------------------------------------------

I press on suggestion text
  Click element  css=span.suggestion

# --- THEN -------------------------------------------------------------------

I see suggestion in search field
  Textfield value should be  xpath=//input[@id='SearchableTextIScroll' and @class="typeahead tt-input"]  welcome

# --- WHEN -------------------------------------------------------------------

I scroll down
  Execute Javascript  window.scrollTo(0,document.body.scrollHeight);

# --- THEN -------------------------------------------------------------------

I see second page with elements
  Textfield value should be  xpath=//input[@id='SearchableTextIScroll' and @class="typeahead tt-input"]  welcome

  Xpath Should Match X Times  //dt[@class="contenttype-document"]  20
  Page should contain  Next 10 items

# --- WHEN -------------------------------------------------------------------

I click on next 10 items button
  Click element  xpath=//a[contains(text(), 'Next 10 items')]

# --- THEN -------------------------------------------------------------------

I see page with all elements
  Page should contain  To The Top
  Page should not contain  Next 10 items
  Textfield value should be  xpath=//input[@id='SearchableTextIScroll' and @class="typeahead tt-input"]  welcome

  Xpath Should Match X Times  //dt[@class="contenttype-document"]  23
  Xpath Should Match X Times  //a[@class="state-None" and contains(text(), 'Welcome to Plone')]  23
  Xpath Should Match X Times  //a[contains(text(), 'user2')]  22
  Xpath Should Match X Times  //a[contains(text(), 'user1')]  1


*** Test Cases ***

Scenario: As user I want to use solr typeahead viewlet to search for something and select autocomplete suggestion
  [Documentation]  Example of a BDD-style (Behavior-driven development) test.
  Given a solr typeahead page with infinite scroll mode
    When I enter part of query
    Then I see autocomplete suggestion
    When I press submit button
    Then I see results by short query
    When I press on suggestion text
    Then I see suggestion in search field
    When I scroll down
    Then I see second page with elements
    When I click on next 10 items button
    Then I see page with all elements
