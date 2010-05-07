# simple benchmarking tests for measuring raw xml parsing speed
# usage:
# $ wget -O parts/test/data.xml 'http://localhost:8983/solr/select/?q=foo&rows=...'
# $ bin/test --tests-pattern=benchmark -v -v

from unittest import TestCase, defaultTestLoader
from collective.solr.parser import SolrResponse
from collective.solr.iterparse import source


print 'Using `iterparse` from `%s`...' % source


class ParserBenchmarks(TestCase):

    data = open('data.xml', 'r').read()

    def test1(self):
        SolrResponse(self.data)

    def test2(self):
        SolrResponse(self.data)

    def test3(self):
        SolrResponse(self.data)

    def test4(self):
        SolrResponse(self.data)

    def test5(self):
        SolrResponse(self.data)


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
