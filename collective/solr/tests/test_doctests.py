from unittest import TestSuite
from zope.testing import doctest
from Testing import ZopeTestCase as ztc
from plone.app.controlpanel.tests.cptc import ControlPanelTestCase
from collective.solr.tests.base import SolrFunctionalTestCase

optionflags = (doctest.REPORT_ONLY_FIRST_FAILURE |
               doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)


def test_suite():
    return TestSuite([
        ztc.FunctionalDocFileSuite(
           'configlet.txt', package='collective.solr.tests',
           test_class=ControlPanelTestCase, optionflags=optionflags),
        ztc.FunctionalDocFileSuite(
           'errors.txt', package='collective.solr.tests',
           test_class=SolrFunctionalTestCase, optionflags=optionflags),
    ])

