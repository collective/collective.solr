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

a default page
  Go To  ${PLONE_URL}
  Wait until page contains element  css=input.typeahead.tt-input


# --- WHEN -------------------------------------------------------------------

I enter part of query
  Input Text  SearchableTextViewlet  Welcom

# --- THEN -------------------------------------------------------------------

I see autocomplete suggestion
  Wait until page contains element  css=div.tt-suggestion.tt-selectable
  Element text should be  css=div.tt-suggestion.tt-selectable  Welcome to Plone

# --- WHEN -------------------------------------------------------------------

I press submit button
  Click element  id=solr-submit-viewlet

# --- THEN -------------------------------------------------------------------

Then I see solr typeahead search page with results by full query
  Location should be  ${PLONE_URL}/solr-typeahead?SearchableText=Welcome%20to%20Plone
  Wait until page contains element  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]
  Textfield value should be  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]  Welcome to Plone

# --- THEN -------------------------------------------------------------------

Then I see solr typeahead search page with results by short query
  Location should be  ${PLONE_URL}/solr-typeahead?SearchableText=Welcom
  Wait until page contains element  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]
  Textfield value should be  xpath=//input[@id='SearchableText' and @class="typeahead tt-input"]  Welcom

# --- WHEN -------------------------------------------------------------------

I press on autocomplete suggestion
  Click element  css=div.tt-suggestion.tt-selectable

*** Test Cases ***************************************************************

Scenario: As user I want to use solr typeahead viewlet to search for something and select autocomplete suggestion
  [Documentation]  Example of a BDD-style (Behavior-driven development) test.
  Given a default page
   When I enter part of query
   Then I see autocomplete suggestion
   When I press on autocomplete suggestion
   Then I see solr typeahead search page with results by full query

Scenario: As user I want to use solr typeahead viewlet to search for something
  [Documentation]  Example of a BDD-style (Behavior-driven development) test.
  Given a default page
   When I enter part of query
   Then I see autocomplete suggestion
   When I press submit button
   Then I see solr typeahead search page with results by short query