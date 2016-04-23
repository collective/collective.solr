# ============================================================================
# EXAMPLE ROBOT TESTS
# ============================================================================
#
# Run this robot test stand-alone:
#
#  $ bin/test -s collective.solr -t test_search.robot --all
#
# Run this robot test with robot server (which is faster):
#
# 1) Start robot server:
#
# $ bin/robot-server --reload-path src collective.solr.testing.COLLECTIVE_SOLR_ROBOT_TESTING
#
# 2) Run robot tests:
#
# $ bin/robot src/collective/solr/tests/robot/test_search.robot
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

Scenario: As anonymous user I can search for a document title
  Given a public document with the title 'Colorless Green Ideas'
    and an anonymous user
   When I search for 'Colorless Green Ideas'
#   Then the search returns '1' results
    and the search results should include 'Colorless Green Ideas'
  Capture screenshot  search_document_title.png

# Scenario: As anonymous user I can search for a term in the document title
#   Given a public document with the title 'Colorless Green Ideas'
#     and an anonymous user
#    When I search for 'Color'
#    Then the search returns '1' results
#     and the search results should include 'Colorless Green Ideas'
#   Capture screenshot  search_document_title_term.png

# Scenario: As anonymous user I can search for a term prefix in the document title
#   Given a public document with the title 'Colorless Green Ideas'
#     and an anonymous user
#    When I search for 'Color'
#    Then the search returns '1' results
#     and the search results should include 'Colorless Green Ideas'
#   Capture screenshot  search_document_title_term_prefix.png

# Scenario: As anonymous user I can search for a term suffix in the document title
#   Given a public document with the title 'Colorless Green Ideas'
#     and an anonymous user
#    When I search for 'less'
#    Then the search returns '1' results
#     and the search results should include 'Colorless Green Ideas'
#   Capture screenshot  search_document_title_term_suffix.png

# Scenario: As anonymous user I can search for a term substring in the document title
#   Given a public document with the title 'Colorless Green Ideas'
#     and an anonymous user
#    When I search for 'lorless'
#    Then the search returns '1' results
#     and the search results should include 'Colorless Green Ideas'
#   Capture screenshot  search_document_title_term_substring.png

# Scenario: As anonymous user I can do a case insensitive search for a document title
#   Given a public document with the title 'Colorless Green Ideas'
#     and an anonymous user
#    When I search for 'colorless green ideas'
#    Then the search returns '1' results
#     and the search results should include 'Colorless Green Ideas'
#   Capture screenshot  search_document_title_case_intesitive.png

# Scenario: As anonymous user I can do a fuzzy search for a document title
#   Given a public document with the title 'Colorless Green Ideas'
#     and an anonymous user
#    When I search for 'Colorless Grean Ideas'
#    Then the search returns '1' results
#     and the search results should include 'Colorless Green Ideas'
#   Capture screenshot  search_document_title_fuzzy.png

# Todo:
# Synonyms
# Phrase Search
# Stemming
# Compound Words
# Suggest
# Autocomplete
# AND concatenation
# OR concatenation
# NOT expression


*** Keywords *****************************************************************


TestSetup
  Open test browser
  a logged in Manager
  Go to  ${PLONE_URL}/@@solr-maintenance/clear
  Wait until page contains  solr index cleared

TestTeardown
  a logged in Manager
  Go to  ${PLONE_URL}/@@solr-maintenance/clear
  Run keywords  Close all browsers


# Given

a public document with the title '${title}'
  Enable autologin as  Manager
  ${uid}=  Create content  type=Document  title=${title}
  Fire transition  ${uid}  publish
  Go to  ${PLONE_URL}/@@solr-maintenance/reindex
  Wait until page contains  solr index rebuilt

an anonymous user
  Disable Autologin


# When

I search for '${searchterm}'
  Go to  ${PLONE_URL}/@@search
  Input text  xpath=//main//input[@name='SearchableText']  ${searchterm}


# Then

the search returns '${result_count}' results
  Wait until keyword succeeds  5s  1s  XPath Should Match X Times  //strong[@id='search-results-number' and contains(.,'${result_count}')]  1  The search should have returned '${result_count}' results.

the search results should include '${term}'
  Wait until page contains element  xpath=//ol[@class='searchResults']/li
  Page should contain  ${term}
  XPath Should Match X Times  //div[@id='search-results']//ol//li//a[contains(., '${term}')]  1  Search results should have contained '${term}'.

the search results should not include '${term}'
  Wait until page contains  Search results
  Page should not contain element  xpath=//*[@class='searchResults']/a[contains(text(), '${term}')]


# Misc

Capture screenshot
  [Arguments]  ${filename}
  Capture Page Screenshot  filename=../../../../docs/_screenshots/${filename}
