from unittest import TestSuite
from zope.testing import doctest
from Testing import ZopeTestCase as ztc
from plone.app.controlpanel.tests.cptc import ControlPanelTestCase
from collective.solr.tests.base import SolrFunctionalTestCase
from collective.solr.tests.utils import solrStatus

optionflags = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    suite = TestSuite([
        ztc.FunctionalDocFileSuite(
           'configlet.txt', package='collective.solr.tests',
           test_class=ControlPanelTestCase, optionflags=optionflags),
        ztc.FunctionalDocFileSuite(
           'errors.txt', package='collective.solr.tests',
           test_class=SolrFunctionalTestCase, optionflags=optionflags),
    ])
    status = solrStatus()
    if status:
        print 'WARNING: solr tests could not be run: "%s".' % status
    else:
        suite.addTest(
            ztc.FunctionalDocFileSuite(
               'search.txt', package='collective.solr.tests',
               test_class=SolrFunctionalTestCase, optionflags=optionflags),
        )
    return suite

