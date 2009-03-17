from unittest import TestSuite, defaultTestLoader
from zope.interface import alsoProvides
from zope.component import getMultiAdapter
from zope.publisher.browser import TestRequest

from collective.solr.tests.utils import pingSolr
from collective.solr.tests.base import SolrTestCase
from collective.solr.browser.interfaces import IThemeSpecific
from collective.solr.dispatcher import solrSearchResults
from collective.solr.utils import activate


class SolrFacettingTests(SolrTestCase):

    def afterSetUp(self):
        activate()
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.maintenance.clear()
        self.maintenance.reindex()

    def beforeTearDown(self):
        activate(active=False)

    def testFacettedSearchWithKeywordArguments(self):
        results = solrSearchResults(SearchableText='News', facet='true',
            facet_field='portal_type')
        self.assertEqual([r.physicalPath for r in results],
            ['/plone/news', '/plone/news/aggregator'])
        types = results.facet_counts['facet_fields']['portal_type']
        self.assertEqual(len(types), 4)
        self.assertEqual(types['Document'], 0)
        self.assertEqual(types['Topic'], 1)

    def testFacettedSearchWithRequestArguments(self):
        request = TestRequest()
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'review_state'
        results = solrSearchResults(request)
        self.assertEqual([r.physicalPath for r in results],
            ['/plone/news', '/plone/news/aggregator'])
        states = results.facet_counts['facet_fields']['review_state']
        self.assertEqual(states, dict(private=0, published=2))

    def checkOrder(self, html, *order):
        for item in order:
            position = html.find(item)
            self.failUnless(position >= 0,
                'menu item "%s" missing or out of order' % item)
            html = html[position:]

    def testFacetsInformationView(self):
        request = TestRequest()
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'portal_type'
        alsoProvides(request, IThemeSpecific)
        view = getMultiAdapter((self.portal, request), name='search-facets')
        view = view.__of__(self.portal)     # needed to traverse `view/`
        results = solrSearchResults(request)
        output = view(results=results)
        self.checkOrder(output, 'portal-searchfacets', 'portal_type',
            'Topic', '1', 'Large Plone Folder', '1')


def test_suite():
    if pingSolr():
        return defaultTestLoader.loadTestsFromName(__name__)
    else:
        return TestSuite()
