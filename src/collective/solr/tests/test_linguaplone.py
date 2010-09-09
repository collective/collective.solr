from collective.solr.tests.utils import pingSolr
from collective.solr.tests.base import SolrTestCase
from collective.solr.tests.layer import lingua

from zope.component import getUtility
from transaction import commit, abort
from Products.CMFCore.utils import getToolByName
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISearch
from collective.solr.dispatcher import solrSearchResults
from collective.solr.utils import activate


class LinguaTests(SolrTestCase):

    layer = lingua

    def afterSetUp(self):
        activate()
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.maintenance.clear()
        self.config = getUtility(ISolrConnectionConfig)
        self.search = getUtility(ISearch)
        # also set up the languages...
        self.setRoles(['Manager'])
        ltool = getToolByName(self.portal, 'portal_languages')
        ltool.manage_setLanguageSettings(defaultLanguage='en',
            supportedLanguages=('en', 'de'))

    def beforeTearDown(self):
        # due to the `commit()` in the tests below the activation of the
        # solr support in `afterSetUp` needs to be explicitly reversed,
        # but first all uncommitted changes made in the tests are aborted...
        abort()
        self.config.active = False
        self.config.async = False
        commit()

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


def test_suite():
    from unittest import TestSuite, defaultTestLoader
    if pingSolr():
        return defaultTestLoader.loadTestsFromName(__name__)
    else:
        return TestSuite()
