# -*- coding: utf-8 -*-

from unittest import TestSuite, defaultTestLoader
from zope.interface import alsoProvides
from zope.component import getMultiAdapter

from collective.solr.solr import SolrException
from collective.solr.tests.utils import pingSolr
from collective.solr.tests.base import SolrTestCase
from collective.solr.browser.interfaces import IThemeSpecific
from collective.solr.browser.facets import SearchBox, SearchFacetsView
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
        self.setRoles(('Manager',))
        self.portal.invokeFactory('Event', id='event1', title='Welcome')
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='Welcome', facet='true',
            facet_field='portal_type')
        self.assertEqual(sorted([r.path_string for r in results]),
            ['/plone/event1', '/plone/front-page'])
        types = results.facet_counts['facet_fields']['portal_type']
        self.assertEqual(types['Document'], 1)
        self.assertEqual(types['Event'], 1)

    def testFacettedSearchWithRequestArguments(self):
        request = self.app.REQUEST
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'review_state'
        results = solrSearchResults(request)
        self.assertEqual(sorted([r.path_string for r in results]),
            ['/plone/news', '/plone/news/aggregator'])
        states = results.facet_counts['facet_fields']['review_state']
        self.assertEqual(states, dict(private=0, published=2))

    def testMultiFacettedSearch(self):
        self.setRoles(('Manager',))
        self.portal.invokeFactory('Event', id='event1', title='Welcome')
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='Welcome', facet='true',
            facet_field=['portal_type', 'review_state'])
        self.assertEqual(sorted([r.path_string for r in results]),
            ['/plone/event1', '/plone/front-page'])
        facets = results.facet_counts['facet_fields']
        self.assertEqual(facets['portal_type']['Event'], 1)
        self.assertEqual(facets['review_state']['published'], 1)

    def testFacettedSearchWithFilterQuery(self):
        request = self.app.REQUEST
        request.form['SearchableText'] = 'News'
        request.form['fq'] = 'portal_type:Topic'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'review_state'
        results = solrSearchResults(request)
        self.assertEqual([r.path_string for r in results],
            ['/plone/news/aggregator'])
        states = results.facet_counts['facet_fields']['review_state']
        self.assertEqual(states, dict(private=0, published=1))

    def testFacettedSearchWithDependencies(self):
        # facets depending on others should not show up initially
        request = self.app.REQUEST
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = ['portal_type',
            'review_state:portal_type']
        view = SearchFacetsView(self.portal, request)
        view.kw = dict(results=solrSearchResults(request))
        facets = [facet['title'] for facet in view.facets()]
        self.assertEqual(facets, ['portal_type'])
        # now again with the required facet selected
        request.form['fq'] = 'portal_type:Topic'
        view.kw = dict(results=solrSearchResults(request))
        facets = [facet['title'] for facet in view.facets()]
        self.assertEqual(facets, ['portal_type', 'review_state'])

    def testFacettedSearchWithUnicodeFilterQuery(self):
        self.portal.news.portal_type = u'Føø'.encode('utf-8')
        self.maintenance.reindex()
        request = self.app.REQUEST
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'portal_type'
        view = SearchFacetsView(self.portal, request)
        view.kw = dict(results=solrSearchResults(request))
        facets = view.facets()
        self.assertEqual(sorted([c['name'] for c in facets[0]['counts']]),
            [u'Føø', 'Topic'])

    def checkOrder(self, html, *order):
        for item in order:
            position = html.find(item)
            self.failUnless(position >= 0,
                'menu item "%s" missing or out of order' % item)
            html = html[position:]

    def testFacetsInformationView(self):
        self.setRoles(('Manager',))
        self.portal.invokeFactory('Event', id='event1', title='Welcome')
        self.maintenance.reindex()
        request = self.app.REQUEST
        request.form['SearchableText'] = 'Welcome'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'portal_type'
        alsoProvides(request, IThemeSpecific)
        view = getMultiAdapter((self.portal, request), name='search-facets')
        view = view.__of__(self.portal)     # needed to traverse `view/`
        results = solrSearchResults(request)
        output = view(results=results)
        self.checkOrder(output, 'portal-searchfacets', 'Content type',
            'Document', '1', 'Event', '1')

    def testFacetFieldsInSearchBox(self):
        request = self.portal.REQUEST
        viewlet = SearchBox(self.portal, request, None, None)
        viewlet = viewlet.__of__(self.portal)   # needed to get security right
        viewlet.update()
        output = viewlet.render()
        self.checkOrder(output,
            '<input', 'name="facet" value="true"',
            '<input', 'value="portal_type"',
            '<input', 'value="review_state"',
            '</form>')
        # try overriding the desired facets in the request
        request.form['facet.field'] = ['foo']
        output = viewlet.render()
        self.checkOrder(output,
            '<input', 'name="facet" value="true"',
            '<input', 'value="foo"',
            '</form>')
        self.failIf('portal_type' in output)

    def testUnknownFacetField(self):
        request = self.app.REQUEST
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'foo'
        alsoProvides(request, IThemeSpecific)
        view = getMultiAdapter((self.portal, request), name='search-facets')
        self.assertRaises(SolrException, solrSearchResults, request)

    def testNoFacetFields(self):
        request = self.app.REQUEST
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = []
        alsoProvides(request, IThemeSpecific)
        view = getMultiAdapter((self.portal, request), name='search-facets')
        view = view.__of__(self.portal)     # needed to traverse `view/`
        output = view(results=solrSearchResults(request))
        self.failIf('portal-searchfacets' in output, output)

    def testEmptyFacetValue(self):
        # let's artificially create an empty value;  while this is a
        # somewhat unrealistic scenario, empty values may very well occur
        # for additional custom indexes...
        self.portal.news.portal_type = ''
        self.maintenance.reindex()
        # after updating the solr index the view can be checked...
        request = self.app.REQUEST
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = 'portal_type'
        alsoProvides(request, IThemeSpecific)
        view = getMultiAdapter((self.portal, request), name='search-facets')
        view = view.__of__(self.portal)     # needed to traverse `view/`
        results = solrSearchResults(request)
        output = view(results=results)
        # the empty facet value should be displayed resulting in
        # only one list item (`<dd>`)
        self.assertEqual(len(output.split('<dd>')), 2)
        # let's also make sure there are no empty filter queries
        self.failIf('fq=portal_type%3A&amp;' in output)

    def testFacetOrder(self):
        request = self.app.REQUEST
        request.form['SearchableText'] = 'News'
        request.form['facet'] = 'true'
        request.form['facet_field'] = ['portal_type', 'review_state']
        alsoProvides(request, IThemeSpecific)
        view = getMultiAdapter((self.portal, request), name='search-facets')
        view = view.__of__(self.portal)     # needed to traverse `view/`
        results = solrSearchResults(request)
        output = view(results=results)
        # the displayed facets should match the given order...
        self.checkOrder(output, 'portal-searchfacets',
            'Content type', 'Review state')
        # let's also try the other way round...
        request.form['facet_field'] = ['review_state', 'portal_type']
        results = solrSearchResults(request)
        output = view(results=results)
        self.checkOrder(output, 'portal-searchfacets',
            'Review state', 'Content type')


def test_suite():
    if pingSolr():
        return defaultTestLoader.loadTestsFromName(__name__)
    else:
        return TestSuite()
