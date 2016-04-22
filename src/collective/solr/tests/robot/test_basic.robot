# ============================================================================
# EXAMPLE ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s collective.solr -t test_basic.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src collective.solr.testing.COLLECTIVE_SOLR_ROBOT_TESTING
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
Resource  Products/CMFPlone/tests/robot/keywords.robot

Library  Remote  ${PLONE_URL}/RobotRemote

Test Setup  Open test browser
Test Teardown  Close all browsers


*** Test Cases ***************************************************************

Scenario: As a manager I can install and enable the add-on

  [Documentation]  Once installed and enabled, searching produces anything since
  ...              there are no content
  Given a logged-in site manager
   When the product is activated in its configlet
    and I search something
   Then the result is empty

Scenario: As a manager once reindexed I get results
  [Documentation]  Once reindexed, I should get some results
  Given a logged-in site manager
    and a folder with a document 'My searchable page'
   When I search something
   Then it returns the result

*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site manager
  Enable autologin as  Manager  Site Administrator  Contributor  Reviewer

# --- WHEN -------------------------------------------------------------------

the product is activated in its configlet
  Go To  ${PLONE_URL}/@@solr-controlpanel

I search something
  Go To  ${PLONE_URL}/@@search
  Input Text  css=.searchPage.form-control  My

I reindex the site content
  Go To  ${PLONE_URL}/@@solr-maintenance/reindex


# --- THEN -------------------------------------------------------------------

the result is empty
  Page should contain  No results were found

it returns the result
  Page should contain  My searchable page
