from unittest import TestSuite, defaultTestLoader
from zope.component import getUtility
from transaction import commit, abort
from DateTime import DateTime
from time import sleep

from collective.solr.tests.utils import pingSolr, numFound
from collective.solr.tests.base import SolrTestCase
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISearch
from collective.solr.dispatcher import solrSearchResults, FallBackException
from collective.solr.indexer import logger as logger_indexer
from collective.solr.manager import logger as logger_manager
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
        self.assertEqual(numFound(result), 8)

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


class SolrErrorHandlingTests(SolrTestCase):

    def testNetworkFailure(self):
        log = []
        def logger(*args):
            log.extend(args)
        logger_indexer.exception = logger
        config = getUtility(ISolrConnectionConfig)
        config.active = True
        self.folder.processForm(values={'title': 'Foo'})
        commit()                    # indexing on commit, schema gets cached
        port = config.port          # remember previous port setting and...
        config.port = 55555         # fake a broken connection or a down server
        manager = getUtility(ISolrConnectionManager)
        manager.closeConnection()   # which would trigger a reconnect
        self.folder.processForm(values={'title': 'Bar'})
        commit()                    # indexing (doesn't) happen on commit
        self.assertEqual(log, ['exception during indexing %r', self.folder,
            'exception during commit'])
        manager.setHost(active=False, port=port)
        commit()                    # undo changes...

    def testNetworkFailureBeforeSchemaCanBeLoaded(self):
        log = []
        def logger(*args):
            log.extend(args)
        logger_indexer.warning = logger
        logger_indexer.exception = logger
        logger_manager.exception = logger
        config = getUtility(ISolrConnectionConfig)
        config.active = True
        manager = getUtility(ISolrConnectionManager)
        manager.getConnection()     # we already have an open connection...
        port = config.port          # remember previous port setting and...
        config.port = 55555         # fake a broken connection or a down server
        manager = getUtility(ISolrConnectionManager)
        manager.closeConnection()   # which would trigger a reconnect
        self.folder.processForm(values={'title': 'Bar'})
        commit()                    # indexing (doesn't) happen on commit
        self.assertEqual(log, ['exception while getting schema',
            'exception while getting schema',
            'unable to fetch schema, skipping indexing of %r', self.folder,
            'exception during commit'])
        manager.setHost(active=False, port=port)
        commit()                    # undo changes...


class SolrServerTests(SolrTestCase):

    def afterSetUp(self):
        activate()
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.maintenance.clear()
        self.config = getUtility(ISolrConnectionConfig)
        self.search = getUtility(ISearch)

    def beforeTearDown(self):
        # due to the `commit()` in the tests below the activation of the
        # solr support in `afterSetUp` needs to be explicitly reversed,
        # but first all uncommitted changes made in the tests are aborted...
        abort()
        self.config.active = False
        self.config.async = False
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

    def testPathSearches(self):
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        search = lambda path: sorted([ r.physicalPath for r in
            solrSearchResults(request, path=path) ])
        self.assertEqual(len(search(path='/plone')), 8)
        self.assertEqual(search(path='/plone/news'),
            ['/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path={'query': '/plone/news'}),
            ['/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path={'query': '/plone/news', 'depth': 0}),
            ['/plone/news'])
        self.assertEqual(search(path={'query': '/plone', 'depth': 1}),
            ['/plone/Members', '/plone/events', '/plone/front-page', '/plone/news'])

    def testLogicalOperators(self):
        self.portal.news.setSubject(('News',))
        self.portal.events.setSubject(('Events',))
        self.portal['front-page'].setSubject(('News', 'Events',))
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        search = lambda subject: sorted([ r.physicalPath for r in
            solrSearchResults(request, Subject=subject) ])
        self.assertEqual(search(dict(operator='and', query=('News',))),
            ['/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='or', query=('News',))),
            ['/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='or', query=('News', 'Events'))),
            ['/plone/events', '/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='and', query=('News', 'Events'))),
            ['/plone/front-page'])

    def testBooleanValues(self):
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        results = solrSearchResults(request, is_folderish=True)
        self.assertEqual(len(results), 7)
        self.failIf('/plone/front-page' in [ r.physicalPath for r in results ])
        results = solrSearchResults(request, is_folderish=False)
        self.assertEqual(sorted([ r.physicalPath for r in results ]),
            ['/plone/front-page'])

    def testSearchSecurity(self):
        self.setRoles(('Manager',))
        wfAction = self.portal.portal_workflow.doActionFor
        wfAction(self.portal.news, 'retract')
        wfAction(self.portal.news.aggregator, 'retract')
        wfAction(self.portal.events, 'retract')
        wfAction(self.portal.events.aggregator, 'retract')
        wfAction(self.portal.events.aggregator.previous, 'retract')
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), 8)
        self.setRoles(())                   # again as anonymous user
        results = self.portal.portal_catalog(request)
        self.assertEqual(sorted([ r.physicalPath for r in results ]),
            ['/plone/Members', '/plone/Members/test_user_1_', '/plone/front-page'])

    def testEffectiveRange(self):
        self.setRoles(('Manager',))
        self.portal.news.setEffectiveDate(DateTime() + 1)
        self.portal.events.setExpirationDate(DateTime() - 1)
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), 8)
        self.setRoles(())                   # again as anonymous user
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), 6)
        paths = [ r.physicalPath for r in results ]
        self.failIf('/plone/news' in paths)
        self.failIf('/plone/events' in paths)
        results = self.portal.portal_catalog(request, show_inactive=True)
        self.assertEqual(len(results), 8)
        paths = [ r.physicalPath for r in results ]
        self.failUnless('/plone/news' in paths)
        self.failUnless('/plone/events' in paths)

    def testAsyncIndexing(self):
        connection = getUtility(ISolrConnectionManager).getConnection()
        self.config.async = True        # enable async indexing
        self.folder.processForm(values={'title': 'Foo'})
        commit()
        # indexing normally happens on commit, but with async indexing
        # enabled search results won't be up-to-date immediately...
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0, 'this test might fail, '
            'especially when run standalone, because the solr indexing '
            'happens too quickly even though it is done asynchronously...')
        # so we'll have to wait a moment for solr to process the update...
        sleep(2)
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)

    def testLimitSearchResults(self):
        self.maintenance.reindex()
        results = self.search('+parentPaths:/plone')
        self.assertEqual(results.numFound, '8')
        self.assertEqual(len(results), 8)
        # now let's limit the returned results
        config = getUtility(ISolrConnectionConfig)
        config.max_results = 2
        results = self.search('+parentPaths:/plone')
        self.assertEqual(results.numFound, '8')
        self.assertEqual(len(results), 2)
        # an explicit value should still override things
        results = self.search('+parentPaths:/plone', rows=5)
        self.assertEqual(results.numFound, '8')
        self.assertEqual(len(results), 5)

    def testSortParameters(self):
        self.maintenance.reindex()
        search = lambda attr, **kw: ', '.join([ getattr(r, attr) for r in
            solrSearchResults(request=dict(SearchableText='"[* TO *]"',
                              path=dict(query='/plone', depth=1)), **kw) ])
        self.assertEqual(search('Title', sort_on='Title'),
            'Events, News, Users, Welcome to Plone')
        self.assertEqual(search('Title', sort_on='Title', sort_order='reverse'),
            'Welcome to Plone, Users, News, Events')
        self.assertEqual(search('getId', sort_on='Title', sort_order='descending'),
            'front-page, Members, news, events')
        self.assertEqual(search('Title', sort_on='Title', sort_limit=2),
            'Events, News')
        self.assertEqual(search('Title', sort_on='Title', sort_order='reverse',
            sort_limit='3'), 'Welcome to Plone, Users, News')


def test_suite():
    if pingSolr():
        return defaultTestLoader.loadTestsFromName(__name__)
    else:
        return TestSuite()

