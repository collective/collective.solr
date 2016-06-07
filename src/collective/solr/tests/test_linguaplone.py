# -*- coding: utf-8 -*-
import unittest

from Products.CMFCore.utils import getToolByName
from collective.solr.dispatcher import solrSearchResults
from collective.solr.interfaces import ISearch
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.testing import HAS_LINGUAPLONE
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from collective.solr.utils import activate
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from transaction import abort
from transaction import commit
from unittest import TestCase
from zope.component import getUtility


class LinguaTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        activate()
        self.portal = self.layer['portal']
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.maintenance.clear()
        self.config = getUtility(ISolrConnectionConfig)
        self.search = getUtility(ISearch)
        # also set up the languages...
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        ltool = getToolByName(self.portal, 'portal_languages')
        ltool.manage_setLanguageSettings(defaultLanguage='en',
                                         supportedLanguages=('en', 'de'))

    def tearDown(self):
        # due to the `commit()` in the tests below the activation of the
        # solr support in `afterSetUp` needs to be explicitly reversed,
        # but first all uncommitted changes made in the tests are aborted...
        abort()
        self.config.active = False
        self.config.async = False
        commit()

    @unittest.skipIf(not HAS_LINGUAPLONE,
                     "LinguaPlone not installed. skipping")
    def testLanguageSearch(self):
        en = self.portal[self.portal.invokeFactory('Document', 'doc')]
        en.update(title='some document', language='en')
        en.reindexObject()
        de = en.addTranslation('de', title='ein dokument')
        de.reindexObject()
        nt = self.portal[self.portal.invokeFactory('Document', 'foo')]
        nt.update(title='doc foo', language='')     # language-neutral
        nt.reindexObject()
        commit()                        # indexing happens on commit

        def search(**kw):
            results = solrSearchResults(SearchableText='do*', **kw)
            return sorted([r.Title for r in results])
        self.assertEqual(search(), ['doc foo', 'some document'])
        self.assertEqual(search(Language=''), ['doc foo'])
        self.assertEqual(search(Language='en'), ['some document'])
        self.assertEqual(search(Language='de'), ['ein dokument'])
        self.assertEqual(search(Language='all'),
                         ['doc foo', 'ein dokument', 'some document'])
