# -*- coding: utf-8 -*-
from collective.solr.browser.interfaces import IThemeSpecific
from collective.solr.testing import COLLECTIVE_SOLR_INTEGRATION_TESTING
from collective.solr.utils import activate
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from zope.component import getMultiAdapter
from zope.interface import directlyProvides

import json
import unittest


class JsonSolrTests(unittest.TestCase):

    layer = COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.app = self.layer['app']
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = \
            self.portal.unrestrictedTraverse('@@solr-maintenance')
        activate()
        self.maintenance.clear()
        self.maintenance.reindex()
        directlyProvides(self.request, IThemeSpecific)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def tearDown(self):
        activate(active=False)

    def afterSetUp(self):
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')

    def beforeTearDown(self):
        pass

    def test_search_view_returns_plone_app_search_view(self):
        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        self.assertTrue(view)

    def test_search_view_with_json_accept_header(self):
        self.request.response.setHeader('Accept', 'application/json')
        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        self.assertEqual(json.loads(view())['data'], [])

    def test_search_view_with_format_json(self):
        self.request.set('format', 'json')
        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        self.assertEqual(json.loads(view())['data'], [])

    def test_search_view_without_param(self):
        self.request.set('format', 'json')
        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        self.assertTrue(view())
        self.assertEqual(json.loads(view())['data'], [])

    def test_search_view_with_empty_param(self):
        self.request.set('format', 'json')
        self.request.set('SearchableText', '')
        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        self.assertTrue(view())
        self.assertEqual(json.loads(view())['data'], [])

    def test_search_view(self):
        self.portal.invokeFactory(
            'Document',
            id='doc1',
            title=u'My First Document',
        )
        self.portal.setDescription(u'This is my first document.')
        self.maintenance.reindex()
        self.request.set('format', 'json')
        self.request.set('SearchableText', 'First')

        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)

        result = json.loads(view())

        self.assertEqual(
            len(result['data']),
            1
        )
        self.assertEqual(
            result['data'][0]['id'],
            u'doc1',
        )
        self.assertEqual(
            result['data'][0]['title'],
            u'My First Document',
        )
        self.assertEqual(
            result['data'][0]['description'],
            u'This is my first document.',
        )
        self.assertEqual(
            result['data'][0]['url'],
            u'{}/doc1'.format(self.portal.absolute_url())
        )
        self.assertEqual(
            result['data'][0]['portal_type'],
            u'Document'
        )

    def test_browser_search_view_suggest(self):
        self.portal.invokeFactory(
            'Document',
            id='doc1',
            title=u'My First Document',
        )
        self.maintenance.reindex()
        self.request.set('format', 'json')
        self.request.set('SearchableText', 'fist')

        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        result = json.loads(view())

        self.assertEqual(
            len(result['data']),
            0
        )
        self.assertTrue(result['suggestions'])
        self.assertEqual(
            [u'first'],
            result['suggestions'].values()[0]['suggestion']
        )

    def test_browser_search_view_suggest_multiple(self):
        self.portal.invokeFactory(
            'Document',
            id='doc1',
            title=u'My farst Document',
        )
        self.portal.invokeFactory(
            'Document',
            id='doc2',
            title=u'My fbrst Document',
        )
        self.maintenance.reindex()
        self.request.set('format', 'json')
        self.request.set('SearchableText', 'first')

        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        result = json.loads(view())

        self.assertEqual(
            len(result['data']),
            0
        )

        self.assertTrue(result['suggestions'])
        self.assertEqual(
            [u'farst', u'fbrst'],
            result['suggestions'].values()[0]['suggestion']
        )
