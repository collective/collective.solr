import doctest
from unittest import TestSuite

from plone.testing import layered

from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

try:
    from Products.CMFPlone import relationhelper  # noqa

    HAS_PLONE6 = True
except ImportError:
    HAS_PLONE6 = False

optionflags = (
    doctest.ELLIPSIS
    | doctest.NORMALIZE_WHITESPACE
    | doctest.REPORT_ONLY_FIRST_FAILURE
    | doctest.IGNORE_EXCEPTION_DETAIL
)


def test_suite():
    suite = TestSuite()
    if HAS_PLONE6:
        # XXX: errors.txt doctest tests won't work with Plone 6 because ZServer is gone
        testfiles = ["configlet.txt"]
    else:
        testfiles = ["errors.txt", "configlet.txt"]

    for testfile in testfiles:
        doc_suite = doctest.DocFileSuite(
            testfile, package="collective.solr.tests", optionflags=optionflags
        )
        layer = layered(doc_suite, layer=LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING)
        suite.addTest(layer)
    return suite
