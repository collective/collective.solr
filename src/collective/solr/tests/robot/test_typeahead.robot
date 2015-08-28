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

*** Settings *****************************************************************

Resource  plone/app/robotframework/selenium.robot
Resource  plone/app/robotframework/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers

*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a solr typeahead page
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

Then I see results by short query
  Location should be  ${PLONE_URL}/solr-typeahead
  Wait until page contains element  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]
  Textfield value should be  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]  Welcom
  Wait until page contains element  css=dt.contenttype-document

  Element should contain  id=search-results-number  23
  Element should contain  css=span.sugg  welcome

  Page should contain  Next 10 items
  Page should contain  [1]
  Page should contain element xpath=//a[@class="solr-batching" and @text()="2"]

  Wait until page contains element  div.qqq


*** Test Cases ***************************************************************

Scenario: As user I want to use solr typeahead viewlet to search for something and select autocomplete suggestion
  [Documentation]  Example of a BDD-style (Behavior-driven development) test.
  Given a solr typeahead page
    When I enter part of query
    Then I see autocomplete suggestion
    When I press submit button
    Then I see results by short query




