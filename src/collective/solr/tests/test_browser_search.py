# -*- coding: UTF-8 -*-
from zope.interface import directlyProvides
from collective.solr.browser.interfaces import IThemeSpecific
from collective.solr.testing import COLLECTIVE_SOLR_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter

import json
import unittest


class SuggestTermsViewIntegrationTest(unittest.TestCase):

    layer = COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request['ACTUAL_URL'] = self.portal.absolute_url()
        directlyProvides(self.request, IThemeSpecific)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

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
        self.assertEqual(json.loads(view()), [])

    def test_search_view_with_format_json(self):
        self.request.set('format', 'json')
        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        self.assertEqual(json.loads(view()), [])

    def test_search_view_without_param(self):
        self.request.set('format', 'json')
        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        self.assertTrue(view())
        self.assertEqual(json.loads(view()), [])

    def test_search_view_with_empty_param(self):
        self.request.set('format', 'json')
        self.request.set('SearchableText', '')
        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)
        self.assertTrue(view())
        self.assertEqual(json.loads(view()), [])

    def test_search_view(self):
        self.portal.invokeFactory(
            'Document',
            id='doc1',
            title=u'My First Document',
        )
        self.portal.setDescription(u'This is my first document.')
        self.request.set('format', 'json')
        self.request.set('SearchableText', 'First')

        view = getMultiAdapter(
            (self.portal, self.request),
            name="search"
        )
        view = view.__of__(self.portal)

        self.assertEqual(
            len(json.loads(view())),
            1
        )
        self.assertEqual(
            json.loads(view())[0]['id'],
            u'doc1',
        )
        self.assertEqual(
            json.loads(view())[0]['title'],
            u'My First Document',
        )
        self.assertEqual(
            json.loads(view())[0]['description'],
            u'This is my first document.',
        )
        self.assertEqual(
            json.loads(view())[0]['url'],
            u'{}/doc1'.format(self.portal.absolute_url())
        )
        self.assertEqual(
            json.loads(view())[0]['portal_type'],
            u'Document'
        )
