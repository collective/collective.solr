# -*- coding: utf-8 -*-
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from plone.testing import layered
from unittest import TestSuite
import doctest

optionflags = (doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE
               | doctest.REPORT_ONLY_FIRST_FAILURE)


def test_suite():
    suite = TestSuite()
    testfiles = [
        'errors.txt',
        'configlet.txt',
        'collections.txt',
    ]
    for testfile in testfiles:
        doc_suite = doctest.DocFileSuite(testfile,
                                         package='collective.solr.tests',
                                         optionflags=optionflags)
        layer = layered(doc_suite,
                        layer=LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING)
        suite.addTest(layer)
    return suite
