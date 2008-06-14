from unittest import TestSuite, defaultTestLoader
from zope.component import getUtility
from transaction import commit

from collective.solr.tests.utils import pingSolr, numFound
from collective.solr.tests.base import SolrTestCase
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISearch
from collective.solr.dispatcher import solrSearchResults, FallBackException
from collective.solr.utils import activate


class SolrMaintenanceTests(SolrTestCase):

    def afterSetUp(self):
        activate()

    def beforeTearDown(self):
        activate(active=False)

    def testClear(self):
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()
        # make sure nothing is indexed
        connection.deleteByQuery('[* TO *]')
        connection.commit()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(numFound(result), 0)
        # now add something...
        connection.add(UID='foo', Title='bar')
        connection.commit()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(numFound(result), 1)
        # and clear things again...
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.clear()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(numFound(result), 0)

    def testReindex(self):
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()
        # make sure nothing is indexed
        connection.deleteByQuery('[* TO *]')
        connection.commit()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(numFound(result), 0)
        # reindex and check again...
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.reindex()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(numFound(result), 9)

    def testPartialReindex(self):
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()
        # make sure nothing is indexed
        connection.deleteByQuery('[* TO *]')
        connection.commit()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(numFound(result), 0)
        # reindex and check again...
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        maintenance = self.portal.unrestrictedTraverse('news/solr-maintenance')
        maintenance.reindex()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(numFound(result), 2)


class SolrServerTests(SolrTestCase):

    def afterSetUp(self):
        activate()
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.maintenance.clear()
        self.search = getUtility(ISearch)

    def beforeTearDown(self):
        # due to the `commit()` in the tests below the activation of the
        # solr support in `afterSetUp` needs to be explicitly reversed...
        activate(active=False)
        commit()

    def testReindexObject(self):
        self.folder.processForm(values={'title': 'Foo'})
        connection = getUtility(ISolrConnectionManager).getConnection()
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0)
        commit()                        # indexing happens on commit
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)

    def testSearchObject(self):
        self.folder.processForm(values={'title': 'Foo'})
        commit()                        # indexing happens on commit
        results = self.search('+Title:Foo')
        self.assertEqual(results.numFound, '1')
        self.assertEqual(results[0].Title, 'Foo')
        self.assertEqual(results[0].UID, self.folder.UID())

    def testSolrSearchResultsFallback(self):
        self.assertRaises(FallBackException, solrSearchResults, dict(foo='bar'))

    def testSolrSearchResults(self):
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='News')
        self.assertEqual([ (r.Title, r.physicalPath) for r in results ],
            [('News', '/plone/news'), ('News', '/plone/news/aggregator')])

    def testPathSearch(self):
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        results = solrSearchResults(request, path='/plone')
        self.assertEqual(len(results), 9)
        results = solrSearchResults(request, path='/plone/news')
        self.assertEqual([ r.physicalPath for r in results ],
            ['/plone/news', '/plone/news/aggregator'])
        results = solrSearchResults(request, path={'query': '/plone/news'})
        self.assertEqual([ r.physicalPath for r in results ],
            ['/plone/news', '/plone/news/aggregator'])
        results = solrSearchResults(request,
            path={'query': '/plone/news', 'depth': 0})
        self.assertEqual([ r.physicalPath for r in results ], ['/plone/news'])
        results = solrSearchResults(request,
            path={'query': '/plone', 'depth': 1})
        self.assertEqual(sorted([ r.physicalPath for r in results ]),
            ['/plone/Members', '/plone/events', '/plone/front-page', '/plone/news'])


def test_suite():
    if pingSolr():
        return defaultTestLoader.loadTestsFromName(__name__)
    else:
        return TestSuite()

