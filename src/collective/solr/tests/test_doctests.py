import doctest
from unittest import TestSuite

from Testing import ZopeTestCase as ztc
from collective.solr.tests.base import SolrFunctionalTestCase
from collective.solr.tests.base import SolrControlPanelTestCase
from collective.solr.tests.utils import pingSolr

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    suite = TestSuite()
    if pingSolr():
        suite.addTest(
            ztc.FunctionalDocFileSuite(
               'configlet.txt', package='collective.solr.tests',
               test_class=SolrControlPanelTestCase, optionflags=optionflags),
        )
        suite.addTest(
            ztc.FunctionalDocFileSuite(
               'errors.txt', package='collective.solr.tests',
               test_class=SolrFunctionalTestCase, optionflags=optionflags),
        )
        suite.addTest(
            ztc.FunctionalDocFileSuite(
               'search.txt', package='collective.solr.tests',
               test_class=SolrFunctionalTestCase, optionflags=optionflags),
        )
        suite.addTest(
            ztc.FunctionalDocFileSuite(
               'conflicts.txt', package='collective.solr.tests',
               test_class=SolrFunctionalTestCase, optionflags=optionflags),
        )
        suite.addTest(
            ztc.FunctionalDocFileSuite(
               'facets.txt', package='collective.solr.tests',
               test_class=SolrFunctionalTestCase, optionflags=optionflags),
        )
        suite.addTest(
            ztc.FunctionalDocFileSuite(
               'dependencies.txt', package='collective.solr.tests',
               test_class=SolrFunctionalTestCase, optionflags=optionflags),
        )
        suite.addTest(
            ztc.FunctionalDocFileSuite(
               'collections.txt', package='collective.solr.tests',
               test_class=SolrFunctionalTestCase, optionflags=optionflags),
        )
    return suite
