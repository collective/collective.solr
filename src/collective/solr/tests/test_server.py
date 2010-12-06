# -*- coding: utf-8 -*-

from unittest import TestSuite, defaultTestLoader
from zope.component import getUtility
from zope.schema.interfaces import IVocabularyFactory
from transaction import commit, abort
from zExceptions import Unauthorized
from DateTime import DateTime
from Missing import MV
from time import sleep
from re import split

from collective.solr.tests.utils import pingSolr, numFound
from collective.solr.tests.base import SolrTestCase
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISearch
from collective.solr.dispatcher import solrSearchResults, FallBackException
from collective.solr.indexer import SolrIndexProcessor
from collective.solr.indexer import logger as logger_indexer
from collective.solr.manager import logger as logger_manager
from collective.solr.flare import PloneFlare
from collective.solr.search import Search
from collective.solr.solr import logger as logger_solr
from collective.solr.utils import activate
from collective.indexing.utils import getIndexer


class SolrMaintenanceTests(SolrTestCase):

    def afterSetUp(self):
        activate()
        manager = getUtility(ISolrConnectionManager)
        self.connection = connection = manager.getConnection()
        # make sure nothing is indexed
        connection.deleteByQuery('+UID:[* TO *]')
        connection.commit()
        result = connection.search(q='+UID:[* TO *]').read()
        self.assertEqual(numFound(result), 0)
        # ignore any generated logging output
        self.response = self.portal.REQUEST.RESPONSE
        self.write = self.response.write
        self.response.write = lambda x: x

    def beforeTearDown(self):
        activate(active=False)
        self.response.write = self.write

    def search(self, query='+UID:[* TO *]'):
        return self.connection.search(q=query).read()

    def counts(self, attributes=None):
        """ crude count of metadata records in the database """
        info = {}
        result = self.search()
        for record in split(r'<(str|date) name="', result)[1:]:
            name = record[:record.find('"')]
            if not attributes or name in attributes:
                info[name] = info.get(name, 0) + 1
        return numFound(result), info

    def testClear(self):
        # add something...
        connection = self.connection
        connection.add(UID='foo', Title='bar')
        connection.commit()
        self.assertEqual(numFound(self.search()), 1)
        # and clear things again...
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.clear()
        self.assertEqual(numFound(self.search()), 0)

    def testReindex(self):
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        # initially the solr index should be empty
        self.assertEqual(numFound(self.search()), 0)
        # after a full reindex all objects should appear...
        maintenance.reindex()
        found, counts = self.counts()
        self.assertEqual(found, 8)
        # let's also make sure the data is complete
        self.assertEqual(counts['Title'], 8)
        self.assertEqual(counts['physicalPath'], 8)
        self.assertEqual(counts['portal_type'], 8)
        self.assertEqual(counts['review_state'], 8)

    def testReindexParameters(self):
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        # the view allos to skip the first n items...
        maintenance.clear()
        maintenance.reindex(skip=2)
        self.assertEqual(numFound(self.search()), 6)
        # and also specify the batch size
        log = []
        def write(msg):
            if 'intermediate' in msg:
                log.append(msg)
        self.response.write = write
        maintenance.clear()
        maintenance.reindex(batch=3)
        self.assertEqual(len(log), 3)
        self.assertEqual(numFound(self.search()), 8)

    def testPartialReindex(self):
        maintenance = self.portal.unrestrictedTraverse('news/solr-maintenance')
        # initially the solr index should be empty
        self.assertEqual(numFound(self.search()), 0)
        # after the partial reindex only some objects should appear...
        maintenance.reindex()
        found, counts = self.counts()
        self.assertEqual(found, 2)
        # let's also make sure their data is complete
        self.assertEqual(counts['Title'], 2)
        self.assertEqual(counts['physicalPath'], 2)
        self.assertEqual(counts['portal_type'], 2)
        self.assertEqual(counts['review_state'], 2)

    def testReindexSingleOrFewAttributes(self):
        # reindexing a set of attributes (or a single one) should not destroy
        # any of the existing data fields, but merely add the new data...
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.reindex(attributes=['UID', 'Title', 'modified'])
        # even after adding only one index all the data should already exist
        attributes = 'Title', 'modified', 'portal_type', 'review_state', 'physicalPath'
        self.assertEqual(self.counts(attributes),
            (8, dict(Title=8, modified=8)))
        # reindexing `portal_type` should add the new metadata column
        maintenance.reindex(attributes=['portal_type'])
        self.assertEqual(self.counts(attributes),
            (8, dict(Title=8, modified=8, portal_type=8)))
        # let's try that again with an EIOW, i.e. `physicalPath`...
        maintenance.reindex(attributes=['physicalPath'])
        self.assertEqual(self.counts(attributes),
            (8, dict(Title=8, modified=8, portal_type=8, physicalPath=8)))
        # as well as with the extra catalog variables...
        maintenance.reindex(attributes=['review_state'])
        self.assertEqual(self.counts(attributes),
            (8, dict(Title=8, modified=8, portal_type=8, physicalPath=8, review_state=8)))

    def testReindexKeepsExistingData(self):
        # add subjects for testing multi-value fields
        self.portal.news.setSubject(['foo', 'bar'])
        attributes = ['UID', 'Title', 'Date', 'Subject']
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.reindex(attributes=attributes)
        # reindexing a single/few attributes shouldn't destroy existing data
        # to check we remember the original results first...
        search = getUtility(ISearch)
        original = search('+UID:[* TO *]', sort='UID asc').results()
        self.assertEqual(original.numFound, '8')
        # let's sync and compare the data from a new search
        maintenance.reindex(attributes=['portal_type', 'review_state'])
        results = search('+UID:[* TO *]', sort='UID asc').results()
        self.assertEqual(results.numFound, '8')
        for idx, result in enumerate(results):
            self.failUnless('portal_type' in result)
            org = original[idx]
            for attr in attributes:
                self.assertEqual(org.get(attr, 42), result.get(attr, 42),
                    '%r vs %r' % (org, result))
        # data not stored (but only indexed) in solr must also be preserved
        # so that querying against the according indices still works...
        results = search('+parentPaths:/plone/news').results()
        self.assertEqual(results.numFound, '2')

    def testReindexSkipsNonReferencableItems(self):
        container = self.folder
        maintenance = container.unrestrictedTraverse('solr-maintenance')
        maintenance.reindex()
        # initially the solr index should only hold the folder
        self.assertEqual(numFound(self.search()), 1)
        # after adding a topic and a criterion, only the topic should
        # get indexed...
        self.setRoles(['Manager'])
        container.invokeFactory('Topic', id='coll', title='a collection')
        crit = container.coll.addCriterion('Type', 'ATPortalTypeCriterion')
        self.assertEqual(crit.UID(), None)
        commit()                        # indexing happens on commit
        self.assertEqual(numFound(self.search()), 2)
        # calling one of a number of methods related to references will
        # generated a UID for the criterion, however, which in turn would
        # cause the object to be added via the "reindex" maintenance view.
        # this shouldn't happen, of course...
        crit.getRefs()
        self.assertNotEqual(crit.UID(), None)
        # however, the call to `manage_afterAdd` generated a UID, which can
        # cause the object to be added via the "reindex" maintenance view...
        maintenance.reindex()
        self.assertEqual(numFound(self.search()), 2)
        criterions = self.search('+portal_type:ATPortalTypeCriterion')
        self.assertEqual(numFound(criterions), 0)
        # the "sync" maintenance view shouldn't add these object, either...
        maintenance.reindex()
        self.assertEqual(numFound(self.search()), 2)
        criterions = self.search('+portal_type:ATPortalTypeCriterion')
        self.assertEqual(numFound(criterions), 0)

    def testDisabledTimeoutDuringReindex(self):
        log = []
        def logger(*args):
            log.extend(args)
        logger_solr.exception = logger
        # specify a very short timeout...
        config = getUtility(ISolrConnectionConfig)
        config.index_timeout = 0.01             # huh, solr is fast!
        # reindexing should disable the timeout...
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.reindex()
        # there should have been no errors...
        self.assertEqual(log, [])
        # let's also reset the timeout and check the results...
        config.index_timeout = None
        self.assertEqual(numFound(self.search()), 8)

    def testDisabledTimeoutDuringSyncing(self):
        log = []
        def logger(*args):
            log.extend(args)
        logger_solr.exception = logger
        # specify a very short timeout...
        config = getUtility(ISolrConnectionConfig)
        config.index_timeout = 0.01             # huh, solr is fast!
        # syncing should disable the timeout...
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.sync()
        # there should have been no errors...
        self.assertEqual(log, [])
        # let's also reset the timeout and check the results...
        config.index_timeout = None
        self.assertEqual(numFound(self.search()), 8)

    def testMetadataHelper(self):
        search = self.portal.portal_catalog.unrestrictedSearchResults
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        items = dict([(b.UID, b.modified) for b in search()])
        metadata = maintenance.metadata('modified', key='UID')
        self.assertEqual(len(metadata), 8)
        self.assertEqual(items, metadata)
        # getting partial metadata should also be possible...
        path = '/plone/news'
        items = dict([(b.UID, b.modified) for b in search(path=path)])
        metadata = maintenance.metadata('modified', key='UID', path=path)
        self.assertEqual(len(metadata), 2)
        self.assertEqual(items, metadata)

    def testDiffHelper(self):
        search = self.portal.portal_catalog.unrestrictedSearchResults
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        full_items = set([b.UID for b in search()])
        news_items = set([b.UID for b in search(path='/plone/news')])
        event_items = set([b.UID for b in search(path='/plone/events')])
        # without an index run all items should need indexing...
        index, reindex, unindex = maintenance.diff(path='/plone')
        self.assertEqual(set(index), full_items)
        self.assertEqual(reindex, [])
        self.assertEqual(unindex, [])
        # after partially reindexing only some are still needed...
        self.portal.unrestrictedTraverse('news/solr-maintenance').reindex()
        index, reindex, unindex = maintenance.diff(path='/plone')
        self.assertEqual(set(index), full_items.difference(news_items))
        self.assertEqual(reindex, [])
        self.assertEqual(unindex, [])
        # a full reindex brings things up to date, i.e. no syncing required...
        maintenance.reindex()
        index, reindex, unindex = maintenance.diff(path='/plone')
        self.assertEqual(index, [])
        self.assertEqual(reindex, [])
        self.assertEqual(unindex, [])
        # after a network outtage some items might need (re|un)indexing...
        activate(active=False)
        self.setRoles(['Manager'])
        self.portal.news.processForm(values={'title': 'Foos'})
        self.portal.manage_delObjects('events')
        commit()                        # indexing happens on commit
        activate(active=True)
        index, reindex, unindex = maintenance.diff(path='/plone')
        self.assertEqual(index, [])
        self.assertEqual(reindex, [self.portal.news.UID()])
        self.assertEqual(set(unindex), event_items)

    def testDiffHelperForPartialContent(self):
        # the helper to determine index differences also works from
        # a given path, returning only partial differences...
        search = self.portal.portal_catalog.unrestrictedSearchResults
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        news_items = set([b.UID for b in search(path='/plone/news')])
        # initially only the items within the given path need indexing...
        index, reindex, unindex = maintenance.diff(path='/plone/news')
        self.assertEqual(set(index), news_items)
        self.assertEqual(reindex, [])
        self.assertEqual(unindex, [])
        # after reindexing that subtree there should be no differences left...
        self.portal.unrestrictedTraverse('news/solr-maintenance').reindex()
        index, reindex, unindex = maintenance.diff(path='/plone/news')
        self.assertEqual(index, [])
        self.assertEqual(reindex, [])
        self.assertEqual(unindex, [])
        # the same is true after a full reindex, of course...
        maintenance.reindex()
        index, reindex, unindex = maintenance.diff(path='/plone/news')
        self.assertEqual(index, [])
        self.assertEqual(reindex, [])
        self.assertEqual(unindex, [])
        # after a network outtage some items might need (re|un)indexing...
        aggregator = self.portal.news.aggregator.UID()
        activate(active=False)
        self.setRoles(['Manager'])
        self.portal.news.processForm(values={'title': 'Foos'})
        self.portal.news.manage_delObjects('aggregator')
        self.portal.manage_delObjects('events')
        commit()                        # indexing happens on commit
        activate(active=True)
        index, reindex, unindex = maintenance.diff(path='/plone/news')
        self.assertEqual(index, [])
        self.assertEqual(reindex, [self.portal.news.UID()])
        self.assertEqual(unindex, [aggregator])


class SolrErrorHandlingTests(SolrTestCase):

    def afterSetUp(self):
        self.config = getUtility(ISolrConnectionConfig)
        self.port = self.config.port        # remember previous port setting
        self.folder.unmarkCreationFlag()    # stop LinguaPlone from renaming

    def beforeTearDown(self):
        manager = getUtility(ISolrConnectionManager)
        manager.setHost(active=False, port=self.port)
        commit()                            # undo port changes...

    def testNetworkFailure(self):
        log = []
        def logger(*args):
            log.extend(args)
        logger_indexer.exception = logger
        logger_solr.exception = logger
        self.config.active = True
        self.folder.processForm(values={'title': 'Foo'})
        commit()                    # indexing on commit, schema gets cached
        self.config.port = 55555    # fake a broken connection or a down server
        manager = getUtility(ISolrConnectionManager)
        manager.closeConnection()   # which would trigger a reconnect
        self.folder.processForm(values={'title': 'Bar'})
        commit()                    # indexing (doesn't) happen on commit
        self.assertEqual(log, ['exception during request %r', log[1],
            'exception during request %r', '<commit/>'])
        self.failUnless('/plone/Members/test_user_1_' in log[1])
        self.failUnless('Bar' in log[1])

    def testNetworkFailureBeforeSchemaCanBeLoaded(self):
        log = []
        def logger(*args):
            log.extend(args)
        logger_indexer.warning = logger
        logger_indexer.exception = logger
        logger_manager.exception = logger
        logger_solr.exception = logger
        self.config.active = True
        manager = getUtility(ISolrConnectionManager)
        manager.getConnection()     # we already have an open connection...
        self.config.port = 55555    # fake a broken connection or a down server
        manager.closeConnection()   # which would trigger a reconnect
        self.folder.processForm(values={'title': 'Bar'})
        commit()                    # indexing (doesn't) happen on commit
        self.assertEqual(log, ['exception while getting schema',
            'unable to fetch schema, skipping indexing of %r', self.folder,
            'exception during request %r', '<commit/>'])


class SolrServerTests(SolrTestCase):

    def afterSetUp(self):
        activate()
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.maintenance.clear()
        self.config = getUtility(ISolrConnectionConfig)
        self.search = getUtility(ISearch)
        self.folder.unmarkCreationFlag()    # stop LinguaPlone from renaming

    def beforeTearDown(self):
        # due to the `commit()` in the tests below the activation of the
        # solr support in `afterSetUp` needs to be explicitly reversed,
        # but first all uncommitted changes made in the tests are aborted...
        abort()
        self.config.active = False
        self.config.async = False
        self.config.auto_commit = True
        commit()

    def testGetData(self):
        manager = getUtility(ISolrConnectionManager)
        fields = sorted([f.name for f in manager.getSchema().fields])
        fields.remove('default')        # remove any copy-fields
        proc = SolrIndexProcessor(manager)
        # without explicit attributes all data should be returned
        data, missing = proc.getData(self.folder)
        self.assertEqual(sorted(data.keys()), fields)
        # with a list of attributes all data should be returned still.  this
        # is because current versions of solr don't support partial updates
        # yet... (see https://issues.apache.org/jira/browse/SOLR-139)
        data, missing = proc.getData(self.folder, ['UID', 'Title'])
        self.assertEqual(sorted(data.keys()), ['Title', 'UID'])
        # however, the reindexing can be stopped if none of the given
        # attributes match an existing solr index...
        data, missing = proc.getData(self.folder, ['Foo', 'Bar'])
        self.assertEqual(data, {})

    def testReindexObject(self):
        self.folder.processForm(values={'title': 'Foo'})
        connection = getUtility(ISolrConnectionManager).getConnection()
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0)
        commit()                        # indexing happens on commit
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)

    def testReindexObjectKeepsExistingData(self):
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()
        search = lambda query: numFound(connection.search(q=query).read())
        # first reindex the object in full
        proc = SolrIndexProcessor(manager)
        proc.reindex(self.folder)
        proc.commit()
        self.assertEqual(search('+Title:Foo'), 0)
        self.assertEqual(search('+parentPaths:/plone'), 1)
        self.assertEqual(search('+portal_type:Folder'), 1)
        # now let's only update one index, which shouldn't change anything...
        self.folder.setTitle('Foo')
        proc.reindex(self.folder, ['UID', 'Title'])
        proc.commit()
        self.assertEqual(search('+Title:Foo'), 1)
        self.assertEqual(search('+parentPaths:/plone'), 1)
        self.assertEqual(search('+portal_type:Folder'), 1)

    def testReindexObjectWithEmptyDate(self):
        # this test passes on 64-bit systems, but fails on 32-bit machines
        # for the same reasons explained in `testDateBefore1000AD`...
        log = []
        def logger(*args):
            log.extend(args)
        logger_indexer.exception = logger
        logger_solr.exception = logger
        self.folder.setModificationDate(None)
        self.folder.setTitle('Foo')
        self.folder.reindexObject(idxs=['modified', 'Title'])
        commit()
        self.assertEqual(log, [])
        self.assertEqual(self.search('+Title:Foo').results().numFound, '1')

    def testDateBefore1000AD(self):
        # AT's default "floor date" of `DateTime(1000, 1)` is converted
        # to different time representations depending on if it's running
        # on 32 or 64 bits (because the seconds since/before epoch are bigger
        # than `sys.maxint` and `DateTime.safegmtime` raises an error in this
        # case, resulting in a different timezone calculation).  while the
        # result is off by 5 days for 64 bits, the one for 32 is even more
        # troublesome.  that's because the resulting date is from december
        # 999 (a.d.), and even though the year is sent with a leading zero
        # to Solr, it's returned without one causing the `DateTime` parser
        # to choke...  please note that this is only the case with Solr 1.4.
        conn = getUtility(ISolrConnectionManager).getConnection()
        conn.add(UID='foo', Title='foo', effective='0999-12-31T22:00:00Z')
        conn.commit()
        self.assertEqual(self.search('+Title:Foo').results().numFound, '1')

    def testCommitWithinConnection(self):
        conn = getUtility(ISolrConnectionManager).getConnection()
        conn.add(UID='foo', Title='foo', commitWithin='1000')
        conn.add(UID='bar', Title='foo', commitWithin='1000')
        conn.flush()
        self.assertEqual(self.search('+Title:Foo').results().numFound, '0')
        sleep(1.5)
        self.assertEqual(self.search('+Title:Foo').results().numFound, '2')

    def testFilterInvalidCharacters(self):
        log = []
        def logger(*args):
            log.extend(args)
        logger_indexer.exception = logger
        logger_solr.exception = logger
        # some control characters make solr choke, for example a form feed
        self.folder.invokeFactory('File', 'foo', title='some text',
            file='page 1 \f page 2 \a')
        commit()                        # indexing happens on commit
        # make sure the file was indexed okay...
        self.assertEqual(log, [])
        # and the contents can be searched
        results = self.search('+portal_type:File').results()
        self.assertEqual(results.numFound, '1')
        self.assertEqual(results[0].Title, 'some text')
        self.assertEqual(results[0].UID, self.folder.foo.UID())
        # clean up in the end...
        self.folder.manage_delObjects('foo')
        commit()

    def testSearchObject(self):
        self.folder.processForm(values={'title': 'Foo'})
        commit()                        # indexing happens on commit
        results = self.search('+Title:Foo').results()
        self.assertEqual(results.numFound, '1')
        self.assertEqual(results[0].Title, 'Foo')
        self.assertEqual(results[0].UID, self.folder.UID())

    def testSearchingTwice(self):
        connection = getUtility(ISolrConnectionManager).getConnection()
        connection.reconnects = 0       # reset reconnect count first
        results = self.search('+Title:Foo').results()
        self.assertEqual(results.numFound, '0')
        self.assertEqual(connection.reconnects, 0)
        results = self.search('+Title:Foo').results()
        self.assertEqual(results.numFound, '0')
        self.assertEqual(connection.reconnects, 0)

    def testSolrSearchResultsFallback(self):
        self.assertRaises(FallBackException, solrSearchResults,
            dict(foo='bar'))

    def testSolrSearchResultsFallbackOnEmptyParameter(self):
        self.assertRaises(FallBackException, solrSearchResults,
            dict(SearchableText=''))

    def testSolrSearchResults(self):
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='News')
        self.assertEqual(sorted([(r.Title, r.physicalPath) for r in results]),
            [('News', '/plone/news'), ('News', '/plone/news/aggregator')])

    def testSolrSearchResultsWithUnicodeTitle(self):
        self.folder.processForm(values={'title': u'Føø'})
        commit()                        # indexing happens on commit
        results = solrSearchResults(SearchableText=u'Føø')
        self.assertEqual([r.Title for r in results], [u'Føø'])

    def testSolrSearchResultsInformation(self):
        self.maintenance.reindex()
        response = solrSearchResults(SearchableText='News', Language='all')
        self.assertEqual(len(response), 2)
        self.assertEqual(response.response.numFound, '2')
        self.failUnless(isinstance(response.responseHeader, dict))
        headers = response.responseHeader
        self.assertEqual(sorted(headers), ['QTime', 'params', 'status'])
        self.assertEqual(headers['params']['q'], '+SearchableText:(news* OR News)')

    def testSolrSearchResultsWithDictRequest(self):
        self.maintenance.reindex()
        results = solrSearchResults({'SearchableText': 'News'})
        self.failUnless([r for r in results if isinstance(r, PloneFlare)])
        self.assertEqual(sorted([(r.Title, r.physicalPath) for r in results]),
            [('News', '/plone/news'), ('News', '/plone/news/aggregator')])

    def testRequiredParameters(self):
        self.maintenance.reindex()
        self.assertRaises(FallBackException, solrSearchResults,
            dict(Title='News'))
        # now let's remove all required parameters and try again
        config = getUtility(ISolrConnectionConfig)
        config.required = []
        results = solrSearchResults(Title='News')
        self.assertEqual(sorted([(r.Title, r.physicalPath) for r in results]),
            [('News', '/plone/news'), ('News', '/plone/news/aggregator')])
        # specifying multiple values should required only one of them...
        config.required = ['Title', 'foo']
        results = solrSearchResults(Title='News')
        self.assertEqual(sorted([(r.Title, r.physicalPath) for r in results]),
            [('News', '/plone/news'), ('News', '/plone/news/aggregator')])
        # but solr won't be used if none of them is present...
        config.required = ['foo', 'bar']
        self.assertRaises(FallBackException, solrSearchResults,
            dict(Title='News'))
        # except if you force it via `use_solr`...
        config.required = ['foo', 'bar']
        results = solrSearchResults(Title='News', use_solr=True)
        self.assertEqual(sorted([(r.Title, r.physicalPath) for r in results]),
            [('News', '/plone/news'), ('News', '/plone/news/aggregator')])
        # which also works if nothing is required...
        config.required = []
        results = solrSearchResults(Title='News', use_solr=True)
        self.assertEqual(sorted([(r.Title, r.physicalPath) for r in results]),
            [('News', '/plone/news'), ('News', '/plone/news/aggregator')])
        # it does respect a `False` though...
        config.required = ['foo', 'bar']
        self.assertRaises(FallBackException, solrSearchResults,
            dict(Title='News', use_solr=False))

    def testPathSearches(self):
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        search = lambda path: sorted([r.physicalPath for r in
            solrSearchResults(request, path=path)])
        self.assertEqual(len(search(path='/plone')), 8)
        self.assertEqual(len(search(path={'query': '/plone', 'depth': -1})), 8)
        self.assertEqual(search(path='/plone/news'),
            ['/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path={'query': '/plone/news'}),
            ['/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path={'query': '/plone/news', 'depth': -1}),
            ['/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path={'query': '/plone/news', 'depth': 0}),
            ['/plone/news'])
        self.assertEqual(search(path={'query': '/plone', 'depth': 1}),
            ['/plone/Members', '/plone/events', '/plone/front-page',
             '/plone/news'])

    def testMultiplePathSearches(self):
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        search = lambda path, **kw: sorted([r.physicalPath for r in
            solrSearchResults(request, path=dict(query=path, **kw))])
        # multiple paths with equal length...
        path = ['/plone/news', '/plone/events']
        self.assertEqual(search(path),
            ['/plone/events', '/plone/events/aggregator',
             '/plone/events/aggregator/previous',
             '/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path, depth=-1),
            ['/plone/events', '/plone/events/aggregator',
             '/plone/events/aggregator/previous',
             '/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path, depth=0),
            ['/plone/events', '/plone/news'])
        self.assertEqual(search(path, depth=1),
            ['/plone/events', '/plone/events/aggregator',
             '/plone/news', '/plone/news/aggregator'])
        # multiple paths with different length...
        path = ['/plone/news', '/plone/events/aggregator']
        self.assertEqual(search(path),
            ['/plone/events/aggregator', '/plone/events/aggregator/previous',
             '/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path, depth=-1),
            ['/plone/events/aggregator', '/plone/events/aggregator/previous',
             '/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(path, depth=0),
            ['/plone/events/aggregator', '/plone/news'])
        self.assertEqual(search(path, depth=1),
            ['/plone/events/aggregator', '/plone/events/aggregator/previous',
             '/plone/news', '/plone/news/aggregator'])
        self.assertEqual(search(['/plone/news', '/plone'], depth=1),
            ['/plone/Members', '/plone/events',
             '/plone/front-page', '/plone/news', '/plone/news/aggregator'])

    def testLogicalOperators(self):
        self.portal.news.setSubject(['News'])
        self.portal.events.setSubject(['Events'])
        self.portal['front-page'].setSubject(['News', 'Events'])
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        search = lambda subject: sorted([r.physicalPath for r in
            solrSearchResults(request, Subject=subject)])
        self.assertEqual(search(dict(operator='and', query=['News'])),
            ['/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='or', query=['News'])),
            ['/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='or', query=['News', 'Events'])),
            ['/plone/events', '/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='and',
            query=['News', 'Events'])), ['/plone/front-page'])

    def testBooleanValues(self):
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        results = solrSearchResults(request, is_folderish=True)
        self.assertEqual(len(results), 7)
        self.failIf('/plone/front-page' in [r.physicalPath for r in results])
        results = solrSearchResults(request, is_folderish=False)
        self.assertEqual(sorted([r.physicalPath for r in results]),
            ['/plone/front-page'])

    def testSearchSecurity(self):
        self.setRoles(['Manager'])
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
        self.assertEqual(sorted([r.physicalPath for r in results]),
            ['/plone/Members', '/plone/Members/test_user_1_',
             '/plone/front-page'])

    def testEffectiveRange(self):
        self.setRoles(['Manager'])
        self.portal.news.setEffectiveDate(DateTime() + 1)
        self.portal.events.setExpirationDate(DateTime() - 1)
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), 8)
        self.setRoles(())                   # again as anonymous user
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), 6)
        paths = [r.physicalPath for r in results]
        self.failIf('/plone/news' in paths)
        self.failIf('/plone/events' in paths)
        results = self.portal.portal_catalog(request, show_inactive=True)
        self.assertEqual(len(results), 8)
        paths = [r.physicalPath for r in results]
        self.failUnless('/plone/news' in paths)
        self.failUnless('/plone/events' in paths)

    def testEffectiveRangeWithSteps(self):
        self.setRoles(['Manager'])
        self.config.effective_steps = 900
        self.portal.news.setEffectiveDate(DateTime() + 1)
        self.portal.events.setExpirationDate(DateTime() - 1)
        self.maintenance.reindex()
        request = dict(SearchableText='"[* TO *]"')
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), 8)
        self.setRoles(())                   # again as anonymous user
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), 6)
        paths = [r.physicalPath for r in results]
        self.failIf('/plone/news' in paths)
        self.failIf('/plone/events' in paths)

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

    def testNoAutoCommitIndexing(self):
        connection = getUtility(ISolrConnectionManager).getConnection()
        self.config.auto_commit = False        # disable committing
        self.folder.processForm(values={'title': 'Foo'})
        commit()
        # no indexing happens, make sure we give the server some time
        sleep(2)
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0)

    def testCommitWithinIndexing(self):
        connection = getUtility(ISolrConnectionManager).getConnection()
        self.config.commit_within = 1000
        self.folder.processForm(values={'title': 'Foo'})
        commit()
        # no indexing happens
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0)
        # but after some time, results are there
        sleep(1.5)
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)

    def testLimitSearchResults(self):
        self.maintenance.reindex()
        results = self.search('+parentPaths:/plone').results()
        self.assertEqual(results.numFound, '8')
        self.assertEqual(len(results), 8)
        # now let's limit the returned results
        config = getUtility(ISolrConnectionConfig)
        config.max_results = 2
        results = self.search('+parentPaths:/plone').results()
        self.assertEqual(results.numFound, '8')
        self.assertEqual(len(results), 2)
        # an explicit value should still override things
        results = self.search('+parentPaths:/plone', rows=5).results()
        self.assertEqual(results.numFound, '8')
        self.assertEqual(len(results), 5)

    def testSortParameters(self):
        self.maintenance.reindex()
        search = lambda attr, **kw: ', '.join([getattr(r, attr, '?') for r in
            solrSearchResults(request=dict(SearchableText='"[* TO *]"',
                              path=dict(query='/plone', depth=1)), **kw)])
        self.assertEqual(search('Title', sort_on='Title'),
            'Events, News, Users, Welcome to Plone')
        self.assertEqual(search('Title', sort_on='Title',
            sort_order='reverse'), 'Welcome to Plone, Users, News, Events')
        self.assertEqual(search('getId', sort_on='Title',
            sort_order='descending'), 'front-page, Members, news, events')
        self.assertEqual(search('Title', sort_on='Title', sort_limit=2),
            'Events, News, ?, ?')
        self.assertEqual(search('Title', sort_on='Title', sort_order='reverse',
            sort_limit='3'), 'Welcome to Plone, Users, News, ?')
        # test sort index aliases
        schema = self.search.getManager().getSchema()
        self.failIf('sortable_title' in schema)
        self.assertEqual(search('Title', sort_on='sortable_title'),
            'Events, News, Users, Welcome to Plone')
        # also make sure a non-existing sort index doesn't break things
        self.failIf('foo' in schema)
        self.assertEqual(len(search('Title', sort_on='foo').split(', ')), 4)

    def testFlareHelpers(self):
        folder = self.folder
        folder.processForm(values={'title': 'Foo'})
        commit()                        # indexing happens on commit
        results = solrSearchResults(SearchableText='Foo')
        self.assertEqual(len(results), 1)
        flare = results[0]
        path = '/'.join(folder.getPhysicalPath())
        self.assertEqual(flare.Title, 'Foo')
        self.assertEqual(flare.getObject(), folder)
        self.assertEqual(flare.getPath(), path)
        self.failUnless(flare.getURL().startswith('http://'))
        self.assertEqual(flare.getURL(), folder.absolute_url())
        self.failUnless(flare.getURL(relative=True).startswith('/'))
        self.assertEqual(flare.getURL(relative=True), path)
        self.failUnless(flare.getURL().endswith(flare.getURL(relative=True)))
        self.assertEqual(flare.getId, folder.getId())
        self.assertEqual(flare.id, folder.getId())

    def testWildcardSearches(self):
        self.maintenance.reindex()
        self.folder.processForm(values={'title': 'Newbie!'})
        commit()                        # indexing happens on commit
        results = solrSearchResults(SearchableText='New*')
        self.assertEqual(len(results), 4)
        self.assertEqual(sorted([i.Title for i in results]),
            ['Newbie!', 'News', 'News', 'Welcome to Plone'])

    def testWildcardSearchesMultipleWords(self):
        self.maintenance.reindex()
        self.folder.processForm(values={'title': 'Brazil Germany'})
        commit()                        # indexing happens on commit
        results = solrSearchResults(SearchableText='Braz*')
        self.assertEqual(len(results), 1)
        results = solrSearchResults(SearchableText='Brazil Germa*')
        self.assertEqual(len(results), 1)

    def testAbortedTransaction(self):
        connection = getUtility(ISolrConnectionManager).getConnection()
        # we cannot use `commit` here, since the transaction should get
        # aborted, so let's make sure processing the queue directly works...
        self.folder.processForm(values={'title': 'Foo'})
        indexer = getIndexer()
        indexer.process()
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0)
        indexer.commit()
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)
        # now let's test aborting, but make sure there's nothing left in
        # the queue (by calling `commit`)
        self.folder.processForm(values={'title': 'Bar'})
        indexer.process()
        result = connection.search(q='+Title:Bar').read()
        self.assertEqual(numFound(result), 0)
        indexer.abort()
        commit()
        result = connection.search(q='+Title:Bar').read()
        self.assertEqual(numFound(result), 0)
        # the old title should still be exist...
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)

    def testTimeoutResetAfterSearch(self):
        self.config.search_timeout = 1      # specify the timeout
        connection = getUtility(ISolrConnectionManager).getConnection()
        self.assertEqual(connection.conn.sock.gettimeout(), None)
        results = self.search('+Title:Foo').results()
        self.assertEqual(results.numFound, '0')
        self.assertEqual(connection.conn.sock.gettimeout(), None)

    def testEmptyStringSearch(self):
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText=' ', path='/plone')
        self.assertEqual(len(results), 8)

    def testSearchableTopic(self):
        self.maintenance.reindex()
        self.setRoles(['Manager'])
        self.folder.invokeFactory('Topic', id='news', title='some news')
        news = self.folder.news
        crit = news.addCriterion('SearchableText', 'ATSimpleStringCriterion')
        crit.setValue('News')
        results = news.queryCatalog()
        self.assertEqual(sorted([(r.Title, r.physicalPath) for r in results]),
            [('News', '/plone/news'), ('News', '/plone/news/aggregator')])

    def testSearchDateRange(self):
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='News',
            created=dict(query=DateTime('1970/02/01'), range='min'))
        self.assertEqual(len(results), 2)

    def testSolrIndexesVocabulary(self):
        vocab = getUtility(IVocabularyFactory, name='collective.solr.indexes')
        indexes = [i.token for i in vocab(self.portal)]
        self.failUnless('SearchableText' in indexes)
        self.failUnless('physicalDepth' in indexes)
        self.failIf('physicalPath' in indexes)

    def testFilterQuerySubstitutionDuringSearch(self):
        self.maintenance.reindex()
        # first set up a logger to be able to test the query parameters
        log = []
        original = Search.search
        def logger(*args, **parameters):
            log.append((args, parameters))
            return original(*args, **parameters)
        Search.__call__ = logger
        # a filter query should be used for `portal_type`;  like plone itself
        # we inject the "friendly types" into the query (in `queryCatalog.py`)
        # by using a keyword parameter...
        request = dict(SearchableText='News')
        results = solrSearchResults(request, portal_type='Topic')
        self.assertEqual([(r.Title, r.physicalPath) for r in results],
            [('News', '/plone/news/aggregator')])
        self.assertEqual(len(log), 1)
        self.assertEqual(log[-1][1]['fq'], ['+portal_type:Topic'], log)
        # let's test again with an already existing filter query parameter
        request = dict(SearchableText='News', fq='+review_state:published')
        results = solrSearchResults(request, portal_type='Topic')
        self.assertEqual([(r.Title, r.physicalPath) for r in results],
            [('News', '/plone/news/aggregator')])
        self.assertEqual(len(log), 2)
        self.assertEqual(sorted(log[-1][1]['fq']),
            ['+portal_type:Topic', '+review_state:published'], log)
        Search.__call__ = original

    def testDefaultOperatorIsOR(self):
        schema = self.search.getManager().getSchema()
        if schema['solrQueryParser'].defaultOperator == 'OR':
            self.folder.invokeFactory('Document', id='doc1', title='Foo')
            self.folder.invokeFactory('Document', id='doc2', title='Bar')
            self.folder.invokeFactory('Document', id='doc3', title='Foo Bar')
            commit()                        # indexing happens on commit
            request = dict(SearchableText='Bar Foo')
            results = solrSearchResults(request)
            self.assertEqual(len(results), 3)

    def testDefaultOperatorIsAND(self):
        schema = self.search.getManager().getSchema()
        if schema['solrQueryParser'].defaultOperator == 'AND':
            self.folder.invokeFactory('Document', id='doc1', title='Foo')
            self.folder.invokeFactory('Document', id='doc2', title='Bar')
            self.folder.invokeFactory('Document', id='doc3', title='Foo Bar')
            commit()                        # indexing happens on commit
            request = dict(SearchableText='Bar Foo')
            results = solrSearchResults(request)
            self.assertEqual(len(results), 1)

    def testExplicitLogicalOperatorQueries(self):
        self.folder.invokeFactory('Document', id='doc1', title='Foo')
        self.folder.invokeFactory('Document', id='doc2', title='Bar')
        self.folder.invokeFactory('Document', id='doc3', title='Foo Bar')
        commit()                        # indexing happens on commit
        request = dict(SearchableText='Bar OR Foo')
        results = solrSearchResults(request)
        self.assertEqual(len(results), 3)
        request = dict(SearchableText='Bar AND Foo')
        results = solrSearchResults(request)
        self.assertEqual(len(results), 1)

    def testMultiValueSearch(self):
        self.setRoles(('Manager',))
        self.portal.invokeFactory('Event', id='event1', title='Welcome')
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='Welcome',
            portal_type=['Event', 'Document'])
        self.assertEqual(len(results), 2)
        self.assertEqual(sorted([r.physicalPath for r in results]),
            ['/plone/event1', '/plone/front-page'])

    def testFlareHasDataForAllMetadataColumns(self):
        # all search results should have metadata for all indices
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='Welcome')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].get('Subject'), MV)
        schema = self.search.getManager().getSchema()
        expected = set(list(schema.stored) + ['score'])     # score gets added
        self.assertEqual(set(results[0].keys()), expected)

    def testSearchWithOnlyFilterQueryParameters(self):
        self.maintenance.reindex()
        # let's remove all required parameters and use a filter query
        config = getUtility(ISolrConnectionConfig)
        config.required = []
        config.filter_queries = ['portal_type', 'Language']
        results = solrSearchResults(portal_type=['Document'])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].physicalPath, '/plone/front-page')

    def testAccessSearchResultsFromPythonScript(self):
        self.maintenance.reindex()
        from Products.PythonScripts.PythonScript import manage_addPythonScript
        manage_addPythonScript(self.folder, 'foo')
        self.folder.foo.write('return [r.Title for r in '
            'context.portal_catalog(SearchableText="News")]')
        self.assertEqual(self.folder.foo(), ['News', 'News'])

    def testSearchForTermWithColon(self):
        self.folder.processForm(values={'title': 'foo:bar'})
        commit()                        # indexing happens on commit
        results = solrSearchResults(SearchableText='foo foo:bar')
        self.assertEqual(sorted([r.Title for r in results]), ['foo:bar'])

    def testBatchedSearchResults(self):
        self.maintenance.reindex()
        search = lambda **kw: [getattr(i, 'Title', None) for i in
            solrSearchResults(SearchableText='a*', sort_on='Title', **kw)]
        self.assertEqual(search(),
            ['Events', 'News', 'Past Events', 'Welcome to Plone'])
        # when a batch size is given, the length should remain the same,
        # but only items in the batch actually exist...
        self.assertEqual(search(b_size=2),
            ['Events', 'News', None, None])
        # given a start value, the batch is moved within the search results
        self.assertEqual(search(b_size=2, b_start=1),
            [None, 'News', 'Past Events', None])

    def testGetObjectOnPrivateObject(self):
        self.maintenance.reindex()
        self.loginAsPortalOwner()
        self.portal.invokeFactory('Document', id='doc', title='Foo')
        commit()                        # indexing happens on commit
        self.login()
        results = solrSearchResults(SearchableText='Foo')
        self.assertEqual(len(results), 1)
        self.assertRaises(Unauthorized, results[0].getObject)


def test_suite():
    if pingSolr():
        return defaultTestLoader.loadTestsFromName(__name__)
    else:
        return TestSuite()
