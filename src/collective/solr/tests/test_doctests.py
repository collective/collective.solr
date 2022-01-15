import doctest
from unittest import TestSuite

from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from plone.testing import layered

optionflags = (
    doctest.ELLIPSIS
    | doctest.NORMALIZE_WHITESPACE
    | doctest.REPORT_ONLY_FIRST_FAILURE
    | doctest.IGNORE_EXCEPTION_DETAIL
)


def test_suite():
    suite = TestSuite()
    testfiles = ["errors.txt", "configlet.txt"]
    for testfile in testfiles:
        doc_suite = doctest.DocFileSuite(
            testfile, package="collective.solr.tests", optionflags=optionflags
        )
        layer = layered(doc_suite, layer=LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING)
        suite.addTest(layer)
    return suite
