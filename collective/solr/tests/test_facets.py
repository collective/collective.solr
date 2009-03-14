from unittest import TestSuite, defaultTestLoader
from zope.interface import alsoProvides
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from collective.solr.tests.utils import pingSolr
from collective.solr.tests.test_server import SolrServerTests
from collective.solr.browser.interfaces import IThemeSpecific
from collective.solr.dispatcher import solrSearchResults


class SolrFacettingTests(SolrServerTests):

    def testFacettedSearchWithKeywordArguments(self):
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='News', facet='true',
            facet_field='portal_type')
        self.assertEqual([r.physicalPath for r in results],
            ['/plone/news', '/plone/news/aggregator'])
        types = results.facet_counts['facet_fields']['portal_type']
        self.assertEqual(len(types), 4)
        self.assertEqual(types['Document'], 0)
        self.assertEqual(types['Topic'], 1)

    def testFacettedSearchWithRequestArguments(self):
        self.maintenance.reindex()
        request = TestRequest()
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'review_state'
        results = solrSearchResults(request)
        self.assertEqual([r.physicalPath for r in results],
            ['/plone/news', '/plone/news/aggregator'])
        states = results.facet_counts['facet_fields']['review_state']
        self.assertEqual(states, dict(private=0, published=2))

    def testFacetsInformationView(self):
        self.maintenance.reindex()
        request = TestRequest()
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'review_state'
        alsoProvides(request, IThemeSpecific)
        view = getMultiAdapter((self.portal, request), name='search-facets')
        view = view.__of__(self.portal)     # needed to traverse `view/`
        results = solrSearchResults(request)
        output = view(results=results)
        self.failUnless('facets foo here!' in output)


def test_suite():
    if pingSolr():
        return defaultTestLoader.loadTestsFromName(__name__)
    else:
        return TestSuite()
