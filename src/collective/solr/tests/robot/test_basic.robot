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
  ...              the content is not indexed yet
  Given a logged-in site manager
   When the product is activated in its configlet
    and I search something
   Then the result is empty

Scenario: As a manager once reindexed I get results
  [Documentation]  Once reindexed, I should get some results
  Given a logged-in site manager
   When I reindex the site content
    and I search something
   Then it returns some results

*** Keywords *****************************************************************

# --- Given ------------------------------------------------------------------

a logged-in site manager
  Enable autologin as  Manager  Site Administrator  Contributor  Reviewer

# --- WHEN -------------------------------------------------------------------

the product is activated in its configlet
  Go To  ${PLONE_URL}/@@solr-controlpanel
  # TODO: It's already activated?

I search something
  Go To  ${PLONE_URL}/@@search
  # TODO: Search something

I reindex the site content
  Go To  ${PLONE_URL}/@@solr-maintenance/reindex


# --- THEN -------------------------------------------------------------------

the result is empty
  # TODO: Test it's empty
  Wait until page contains  You are now logged in
  Page should contain  You are now logged in

it returns some results
  # TODO: Test results are shown
