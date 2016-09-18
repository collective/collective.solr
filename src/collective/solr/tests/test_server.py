# -*- coding: utf-8 -*-
from DateTime import DateTime
from Missing import MV
from Products.CMFCore.utils import getToolByName
from collective.indexing.queue import getQueue
from collective.indexing.queue import processQueue
from collective.solr.dispatcher import FallBackException
from collective.solr.dispatcher import solrSearchResults
from collective.solr.flare import PloneFlare
from collective.solr.indexer import SolrIndexProcessor
from collective.solr.indexer import DefaultAdder, BinaryAdder
from collective.solr.indexer import logger as logger_indexer
from collective.solr.interfaces import ISearch
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrAddHandler
from collective.solr.manager import logger as logger_manager
from collective.solr.parser import SolrResponse
from collective.solr.search import Search
from collective.solr.solr import logger as logger_solr
from collective.solr.testing import activateAndReindex
from collective.solr.testing import HAS_LINGUAPLONE
from collective.solr.testing import HAS_PAC
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from collective.solr.testing import set_attributes
from collective.solr.tests.utils import numFound
from collective.solr.utils import activate
from collective.solr.utils import getConfig
from operator import itemgetter
from plone import api
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.namedfile.file import NamedBlobFile
from re import split
from time import sleep
from transaction import abort
from transaction import commit
from unittest import TestCase
from zExceptions import Unauthorized
from zope.component import getUtility, queryAdapter
from zope.interface import implements
from zope.schema.interfaces import IVocabularyFactory
from Products.Archetypes.interfaces import IBaseObject


DEFAULT_OBJS = [
    {'Title': 'News', 'getId': 'aggregator', 'Type': 'Collection',
     'portal_type': 'Collection', 'depth': 1},
    {'Title': 'Welcome to Plone', 'getId': 'front-page', 'Type': 'Page',
     'portal_type': 'Document', 'depth': 0},
    {'Title': 'Events', 'getId': 'aggregator', 'Type': 'Collection',
     'portal_type': 'Collection', 'depth': 1},
    {'Title': 'Previous', 'getId': 'previous', 'Type': 'Page',
     'portal_type': 'Document', 'depth': 1},
    {'Title': 'EventsFolder', 'getId': 'events', 'Type': 'Folder',
     'portal_type': 'Folder', 'depth': 0},
    {'Title': 'NewsFolder', 'getId': 'news', 'Type': 'Folder',
     'portal_type': 'Folder', 'depth': 0}]
if not HAS_PAC:
    DEFAULT_OBJS.extend([
        {'Title': 'test_user_1_', 'getId': 'test_user_1_', 'Type': 'Folder',
         'portal_type': 'Folder', 'depth': 1},
        {'Title': '', 'getId': 'Members', 'Type': 'Folder',
         'portal_type': 'Folder', 'depth': 0}])


class RaisingAdder(DefaultAdder):
    """AddHandler that raises an exception when called
    """

    implements(ISolrAddHandler)

    def __call__(self, conn, **data):
        raise Exception('Test')


class SolrMaintenanceTests(TestCase):
    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.invokeFactory('Folder', id='folder')
        commit()
        self.folder = self.portal.folder
        self.folder.review_state = 'published'
        self.config = getConfig()
        activateAndReindex(self.portal)
        manager = getUtility(ISolrConnectionManager)
        self.connection = connection = manager.getConnection()
        # make sure nothing is indexed
        connection.deleteByQuery('+UID:[* TO *]')
        connection.commit()
        result = connection.search(q='+UID:[* TO *]').read()
        self.assertEqual(numFound(result), 0)
        # ignore any generated logging output
        self.response = self.request.RESPONSE
        self.write = self.response.write
        self.response.write = lambda x: x  # temporarily ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')

    def tearDown(self):
        activate(active=False)
        self.response.write = self.write
        if getattr(self.search, 'config', None) is not None:
            self.search.config = None

    def search(self, query='+UID:[* TO *]'):
        return self.connection.search(q=query).read()

    def counts(self):
        """ crude count of metadata records in the database """
        info = {}
        result = self.search()
        for record in split(r'<(str|date) name="', result)[1:]:
            name = record[:record.find('"')]
            info[name] = info.get(name, 0) + 1
        return numFound(result), info

    def testClear(self):
        # add something...
        connection = self.connection
        connection.add(UID='foo', Title='bar')
        connection.commit()
        self.assertEqual(numFound(self.search()), 1)
        # and clear things again...
        self.maintenance.clear()
        self.assertEqual(numFound(self.search()), 0)

    def testReindex(self):
        # initially the solr index should be empty
        self.assertEqual(numFound(self.search()), 0)
        # after a full reindex all objects should appear...
        self.maintenance.reindex()
        found, counts = self.counts()
        self.assertEqual(found, len(DEFAULT_OBJS))
        # let's also make sure the data is complete
        self.assertEqual(counts['Title'], len(DEFAULT_OBJS))
        self.assertEqual(counts['path_string'], len(DEFAULT_OBJS))
        self.assertEqual(counts['portal_type'], len(DEFAULT_OBJS))
        self.assertEqual(counts['review_state'], len(DEFAULT_OBJS))

    def testReindexParameters(self):
        # the view allows to skip the first n items...
        self.maintenance.clear()
        self.maintenance.reindex(skip=2)
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS)-2)
        # or to limit to n items...
        self.maintenance.clear()
        self.maintenance.reindex(limit=2)
        self.assertEqual(numFound(self.search()), 2)
        # or both
        self.maintenance.clear()
        self.maintenance.reindex(skip=2, limit=2)
        self.assertEqual(numFound(self.search()), 2)
        # and also specify the batch size
        log = []

        def write(msg):
            if 'intermediate' in msg:
                log.append(msg)
        self.response.write = write
        self.maintenance.clear()
        self.maintenance.reindex(batch=3)
        self.assertEqual(len(log), 3)
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS))

    def testReindexPortalTypesParameters(self):
        # initially the solr index should be empty
        self.assertEqual(numFound(self.search()), 0)

        # first test the only_portal_types parameter
        self.maintenance.reindex(only_portal_types=[])
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS))
        self.maintenance.clear()

        self.maintenance.reindex(only_portal_types=['Folder'])
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS)-3)
        self.maintenance.clear()

        self.maintenance.reindex(only_portal_types=['Folder', 'Collection'])
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS)-1)
        self.maintenance.clear()

        self.maintenance.reindex(
            only_portal_types=['Folder', 'Collection', 'NotExistingPortalType']
        )
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS)-1)
        self.maintenance.clear()

        # then the ignore_portal_types
        self.maintenance.reindex(ignore_portal_types=[])
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS))
        self.maintenance.clear()

        self.maintenance.reindex(ignore_portal_types=['Folder'])
        self.assertEqual(numFound(self.search()), 3)
        self.maintenance.clear()

        self.maintenance.reindex(ignore_portal_types=['Folder', 'Collection'])
        self.assertEqual(numFound(self.search()), 1)
        self.maintenance.clear()

        self.maintenance.reindex(
            ignore_portal_types=['Folder', 'Collection',
                                 'NotExistingPortalType']
        )
        self.assertEqual(numFound(self.search()), 1)
        self.maintenance.clear()

        # and then both, which is not supported
        self.assertRaises(ValueError, self.maintenance.reindex,
                          ignore_portal_types=['Collection'],
                          only_portal_types=['Folder'])

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
        self.assertEqual(counts['path_string'], 2)
        self.assertEqual(counts['portal_type'], 2)
        self.assertEqual(counts['review_state'], 2)

    def testReindexKeepsBoostValues(self):
        # Disable atomic updates, in order to test the index time boosting.
        config = getConfig()
        config.atomic_updates = False

        # "special" documents get boosted during indexing...
        from Products.PythonScripts.PythonScript import PythonScript
        name = 'solr_boost_index_values'
        self.portal[name] = PythonScript(name)
        self.portal[name].write(
            "##parameters=data\n"
            "return {'': 100} "
            "if data.get('getId', '') == 'special' else {}")
        self.folder.invokeFactory('Document', id='dull', title='foo',
                                  description='the bar is missing here')
        self.folder.invokeFactory('Document', id='special', title='bar',
                                  description='another foo, this time visible')
        commit()
        # so even though the title ranks higher than the description...
        search = lambda: [result['getId'] for result in
                          getUtility(ISearch)
                          ('Title:foo^2 OR Description:foo').results()]
        # so overall the "special" document should be listed first...
        self.assertEqual(search(), ['special', 'dull'])
        # reindexing should keep the boost values intact...
        self.maintenance.reindex()
        self.assertEqual(search(), ['special', 'dull'])
        # cleanup
        del self.portal[name]

    def testReindexAddHandlers(self):
        """ Add handlers adapt Product.Archetypes.interfaces.IBaseObject.
        This interfaces is not implemented by p.a.contenttypes in Plone 5.0.x.
        As a result, the DefaultAdder is used for all p.a.contenttypes content.
        """
        self.folder.invokeFactory('Image', id='dull', title='foo',
                                  description='the bar is missing here')
        self.assertEqual(
            queryAdapter(self.folder, ISolrAddHandler, name='Folder'),
            None)
        self.assertEqual(
            queryAdapter(self.portal['front-page'], ISolrAddHandler,
                         name='Document'),
            None)
        self.assertTrue(isinstance(
            queryAdapter(self.folder.dull, ISolrAddHandler, name='Image'),
            BinaryAdder))

    def testReindexIgnoreExceptions(self):
        self.folder.invokeFactory('Image', id='dull', title='foo',
                                  description='the bar is missing here')
        sm = self.portal.getSiteManager()
        if api.env.plone_version() >= '5.0':
            from plone.app.contenttypes.interfaces import IImage
            iface = IImage
        else:
            iface = IBaseObject
        sm.registerAdapter(RaisingAdder,
                           required=(iface,),
                           name='Image')
        # ignore_exceptions=False should raise the handler's exception,
        # thereby aborting the reindex tx
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.assertRaises(Exception,
                          maintenance.reindex,
                          ignore_exceptions=False)
        # ignore_exceptions=True should commit the reindex tx.
        # The object causing the exception will not be indexed
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.reindex(ignore_exceptions=True)
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS))
        # restore defaults
        sm.unregisterAdapter(RaisingAdder,
                             required=(iface,),
                             name='Image')

    def testDisabledTimeoutDuringReindex(self):
        log = []

        def logger(*args):
            log.extend(args)
        logger_solr.exception = logger
        # specify a very short timeout...
        config = getConfig()
        config.index_timeout = 0.01             # huh, solr is fast!
        # reindexing should disable the timeout...
        self.maintenance.reindex()
        # there should have been no errors...
        self.assertEqual(log, [])
        # let's also reset the timeout and check the results...
        config.index_timeout = None
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS))

    def testDisabledTimeoutDuringSyncing(self):
        log = []

        def logger(*args):
            log.extend(args)
        logger_solr.exception = logger
        # specify a very short timeout...
        config = getConfig()
        config.index_timeout = 0.01             # huh, solr is fast!
        # syncing should disable the timeout...
        self.maintenance.sync()
        # there should have been no errors...
        self.assertEqual(log, [])
        # let's also reset the timeout and check the results...
        config.index_timeout = None
        self.assertEqual(numFound(self.search()), len(DEFAULT_OBJS))

    def test_sync(self):
        search = self.portal.portal_catalog.unrestrictedSearchResults
        items = dict([(b.UID, b.modified) for b in search()])
        self.assertEqual(len(items), len(DEFAULT_OBJS))
        self.assertEqual(numFound(self.search()), 0)
        self.maintenance.sync()
        found, counts = self.counts()
        self.assertEqual(found, len(DEFAULT_OBJS))

    def test_sync_update(self):
        self.maintenance.sync()
        found, counts = self.counts()
        self.assertEqual(found, len(DEFAULT_OBJS))
        # after a network outage some items might need (re|un)indexing...
        activate(active=False)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        set_attributes(self.portal.news, values={'title': 'Foos'})
        # we only have minute based time resolution, so force an older date
        self.portal.news.setModificationDate(DateTime() - 2)
        self.portal.news.reindexObject(idxs=['modified'])
        self.portal.manage_delObjects('events')
        commit()
        activate(active=True)
        self.maintenance.sync()
        response = SolrResponse(self.search())
        self.assertEqual(len(response), len(DEFAULT_OBJS)-2)
        results = response.results()
        news_uid = self.portal.news.UID()
        news_result = [r for r in results if r['UID'] == news_uid][0]
        self.assertEqual(news_result['Title'], 'Foos')
        results = [(r.path_string, r.modified) for r in results]
        for path, solr_mod in results:
            obj = self.portal.unrestrictedTraverse(path)
            obj_mod = obj.modified().toZone('UTC').millis() / 1000
            solr_mod = solr_mod.toZone('UTC').millis() / 1000
            self.assertEqual(solr_mod, obj_mod)


class SolrErrorHandlingTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.invokeFactory('Folder', id='folder')
        self.folder = self.portal.folder
        self.config = getConfig()
        self.port = self.config.port        # remember previous port setting
        if HAS_LINGUAPLONE:
            self.folder.unmarkCreationFlag()  # stop LinguaPlone from renaming
        # Prevent collective indexing queues to pile up for folder creation
        commit()

    def tearDown(self):
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
        self.portal.invokeFactory('Folder', id='tnf', title='Foo')
        commit()                    # indexing on commit, schema gets cached
        self.config.port = 55555    # fake a broken connection or a down server  # noqa
        manager = getUtility(ISolrConnectionManager)
        manager.closeConnection()   # which would trigger a reconnect
        self.portal.invokeFactory('Folder', id='tnf2', title='Bar')
        commit()                    # indexing (doesn't) happen on commit

        # INFO:
        # Due the "atomic update" feature the indexing mechanism catches the
        # socket error, instead of the connection.
        # This also means we do not have the payload sent to solr at this
        # place.
        self.assertTrue('exception during indexing %r' in log)
        self.assertTrue('exception during request %r' in log)

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
        self.config.port = 55555    # fake a broken connection or a down server  # noqa
        manager.closeConnection()   # which would trigger a reconnect
        self.portal.invokeFactory('Folder', id='tnfb', title='Bar')
        commit()                    # indexing (doesn't) happen on commit
        self.assertTrue(
            'exception while getting schema',
            'unable to fetch schema, '
            'skipping indexing of {}'.format(self.portal.tnfb) in log
        )
        self.assertTrue('exception during request %r' in log)


class SolrServerTests(TestCase):
    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        activateAndReindex(self.portal)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        login(self.portal, 'user1')
        self.portal.news.invokeFactory('Folder', id='folder')
        wfAction = self.portal.portal_workflow.doActionFor
        wfAction(self.portal.news.folder, 'publish')
        login(self.portal, TEST_USER_NAME)
        self.folder = self.portal.news.folder
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.maintenance.clear()
        self.config = getConfig()
        self.search = getUtility(ISearch)
        if HAS_LINGUAPLONE:
            self.folder.unmarkCreationFlag()  # stop LinguaPlone from renaming

    def tearDown(self):
        # due to the `commit()` in the tests below the activation of the
        # solr support in `afterSetUp` needs to be explicitly reversed,
        # but first all uncommitted changes made in the tests are aborted...
        abort()
        self.config.active = False
        self.config.async = False
        self.config.auto_commit = True
        if getattr(self.search, 'config', None) is not None:
            self.search.config = None
        commit()

    def testGetData(self):
        manager = getUtility(ISolrConnectionManager)
        fields = sorted([f.name for f in manager.getSchema().fields])
        # remove copy-field
        fields.remove('default')
        # remove field not defined for a folder
        fields.remove('getRemoteUrl')
        # remove _version_ field
        fields.remove('_version_')
        if HAS_PAC:
            # remove getIcon which is defined for Plone 5 only
            fields.remove('getIcon')
            # remove searchwords which is defined for Plone 5 only
            fields.remove('searchwords')

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
        self.portal.invokeFactory('Document', id='foo', title='Foo')
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
        self.assertEqual(search('+path_parents:\/plone'), 1)
        self.assertEqual(search('+portal_type:Folder'), 1)
        # now let's only update one index, which shouldn't change anything...
        set_attributes(self.folder, values={'title': 'Foo'})
        proc.reindex(self.folder, ['UID', 'Title'])
        proc.commit()
        self.assertEqual(search('+Title:Foo'), 1)
        self.assertEqual(search('+path_parents:\/plone'), 1)
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
        set_attributes(self.folder, values={'title': 'Foo'})
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
        sleep(3.0)
        self.assertEqual(self.search('+Title:Foo').results().numFound, '2')

    def testFilterInvalidCharacters(self):
        log = []

        def logger(*args):
            log.extend(args)
        logger_indexer.exception = logger
        logger_solr.exception = logger
        # some control characters make solr choke, for example a form feed
        self.folder.invokeFactory('File', 'foo', title='some text')
        data = 'page 1 \f page 2 \a'
        if api.env.plone_version() >= '5.0':
            self.folder.foo.file = NamedBlobFile(data=data,
                                                 filename=u'file.pdf')
        else:
            self.folder.foo.file = data
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
        self.portal.invokeFactory('Document', id='foo', title='Foo')
        commit()                        # indexing happens on commit
        results = self.search('+Title:Foo').results()
        self.assertEqual(results.numFound, '1')
        self.assertEqual(results[0].Title, 'Foo')
        self.assertEqual(results[0].UID, self.portal.foo.UID())

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
        self.assertEqual(sorted([(r.Title, r.path_string) for r in results]),
                         [('News', '/plone/news/aggregator'),
                          ('NewsFolder', '/plone/news')])

    def testSolrSearchResultsWithUnicodeTitle(self):
        self.portal.invokeFactory('Document', id='fs', title=u'Føø sekretær')
        commit()
        results = solrSearchResults(SearchableText=u'Føø')
        self.assertEqual([r.Title for r in results], [u'Føø sekretær'])
        results = solrSearchResults(SearchableText=u'foo')
        self.assertEqual([r.Title for r in results], [u'Føø sekretær'])
        results = solrSearchResults(SearchableText=u'Sekretær')
        self.assertEqual([r.Title for r in results], [u'Føø sekretær'])
        results = solrSearchResults(SearchableText=u'Sekretaer')
        self.assertEqual([r.Title for r in results], [u'Føø sekretær'])
        # second set of characters
        self.portal.invokeFactory('Document', id='ab', title=u'Åge Þor')
        commit()
        results = solrSearchResults(SearchableText=u'Åge')
        self.assertEqual([r.Title for r in results], [u'Åge Þor'])
        results = solrSearchResults(SearchableText=u'age')
        self.assertEqual([r.Title for r in results], [u'Åge Þor'])
        results = solrSearchResults(SearchableText=u'Þor')
        self.assertEqual([r.Title for r in results], [u'Åge Þor'])
        results = solrSearchResults(SearchableText=u'thor')
        self.assertEqual([r.Title for r in results], [u'Åge Þor'])

    def testSolrSearchResultsInformationWithoutCustomSearchPattern(self):
        self.maintenance.reindex()
        self.config.search_pattern = None
        query = {'SearchableText': 'News'}
        if HAS_LINGUAPLONE:
            query['Language'] = 'all'
        response = solrSearchResults(**query)
        self.assertEqual(len(response), 2)
        self.assertEqual(response.response.numFound, '2')
        self.assertTrue(isinstance(response.responseHeader, dict))
        headers = response.responseHeader
        self.assertEqual(sorted(headers), ['QTime', 'params', 'status'])
        self.assertEqual(headers['params']['q'],
                         '+SearchableText:(news* OR News)')

    def testSolrSearchResultsInformationForCustomSearchPattern(self):
        self.maintenance.reindex()
        self.config.search_pattern = u'(Title:{value}^5 OR getId:{value})'
        # for single-word searches we get both, wildcards & the custom pattern
        kw_query = {'SearchableText': 'news'}
        if HAS_LINGUAPLONE:
            kw_query['Language'] = 'all'
        response = solrSearchResults(**kw_query)
        query = response.responseHeader['params']['q']
        self.assertEqual(query, '(Title:(news* OR news)^5 '
                         'OR getId:(news* OR news))')
        # the pattern is applied for multi-word searches
        kw_query['SearchableText'] = 'foo bar'
        response = solrSearchResults(**kw_query)
        query = response.responseHeader['params']['q']
        self.assertEqual(query,
                         '(Title:((foo* OR foo) (bar* OR bar))^5 OR '
                         'getId:((foo* OR foo) (bar* OR bar)))')
        # extra parameters should be unaffected
        kw_query['SearchableText'] = '"news"'
        kw_query['Type'] = 'xy'
        response = solrSearchResults(**kw_query)
        query = response.responseHeader['params']['q']
        self.assertEqual(query, '+Type:xy (Title:"news"^5 OR getId:"news")')
        del kw_query['Type']
        # both value and base_value work
        self.config.search_pattern = u'(Title:{value} OR getId:{base_value})'
        kw_query['SearchableText'] = 'news'
        response = solrSearchResults(**kw_query)
        query = response.responseHeader['params']['q']
        self.assertEqual(query, '(Title:(news* OR news) OR getId:(news))')
        # and they handle wildcards as advertised
        kw_query['SearchableText'] = 'news*'
        response = solrSearchResults(**kw_query)
        query = response.responseHeader['params']['q']
        self.assertEqual(query, '(Title:(news*) OR getId:(news))')
        kw_query['SearchableText'] = '*news*'
        response = solrSearchResults(**kw_query)
        query = response.responseHeader['params']['q']
        self.assertEqual(query, '(Title:(news*) OR getId:(news))')

    def testSolrSearchResultsWithDictRequest(self):
        self.maintenance.reindex()
        results = solrSearchResults({'SearchableText': 'News'})
        self.assertTrue([r for r in results if isinstance(r, PloneFlare)])
        self.assertEqual(sorted([(r.Title, r.path_string) for r in results]),
                         [('News', '/plone/news/aggregator'),
                          ('NewsFolder', '/plone/news')])

    def testSolrSearchResultsWithCustomSearchPattern(self):
        self.maintenance.reindex()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Document', id='doc1', title='foo',
                                  description='the bar is missing here')
        self.folder.invokeFactory('Document', id='doc2', title='bar',
                                  description='another foo, this time visible')
        commit()                        # indexing happens on commit
        # first we rank title higher than the description...
        self.config.search_pattern = u'(Title:{value}^5 OR Description:{value})'  # noqa
        search = lambda term: [r.getId for r in
                               solrSearchResults(SearchableText=term)]
        self.assertEqual(search('foo'), ['doc1', 'doc2'])
        self.assertEqual(search('bar'), ['doc2', 'doc1'])
        # now let's try changing the pattern...
        self.config.search_pattern = u'(Description:{value}^5 OR Title:{value})'  # noqa
        self.assertEqual(search('foo'), ['doc2', 'doc1'])
        self.assertEqual(search('bar'), ['doc1', 'doc2'])

    def testRequiredParameters(self):
        self.maintenance.reindex()
        self.assertRaises(FallBackException, solrSearchResults,
                          dict(Title='News'))
        # now let's remove all required parameters and try again
        config = getConfig()
        config.required = []
        results = solrSearchResults(Title='News')
        self.assertEqual(sorted([(r.Title, r.path_string) for r in results]),
                         [('News', '/plone/news/aggregator')])
        # specifying multiple values should required only one of them...
        config.required = [u'Title', u'foo']
        results = solrSearchResults(Title='News')
        self.assertEqual(sorted([(r.Title, r.path_string) for r in results]),
                         [('News', '/plone/news/aggregator')])
        # but solr won't be used if none of them is present...
        config.required = [u'foo', u'bar']
        self.assertRaises(FallBackException, solrSearchResults,
                          dict(Title='News'))
        # except if you force it via `use_solr`...
        config.required = [u'foo', u'bar']
        results = solrSearchResults(Title='News', use_solr=True)
        self.assertEqual(sorted([(r.Title, r.path_string) for r in results]),
                         [('News', '/plone/news/aggregator')])
        # which also works if nothing is required...
        config.required = []
        results = solrSearchResults(Title='News', use_solr=True)
        self.assertEqual(sorted([(r.Title, r.path_string) for r in results]),
                         [('News', '/plone/news/aggregator')])
        # it does respect a `False` though...
        config.required = [u'foo', u'bar']
        self.assertRaises(FallBackException, solrSearchResults,
                          dict(Title='News', use_solr=False))

    def testPathSearches(self):
        self.maintenance.reindex()
        request = dict(SearchableText='[* TO *]')
        search = lambda path: sorted([r.path_string for r in
                                      solrSearchResults(request, path=path)])
        self.assertEqual(len(search(path='/plone')), len(DEFAULT_OBJS))
        self.assertEqual(len(search(path={'query': '/plone', 'depth': -1})),
                         len(DEFAULT_OBJS))
        self.assertEqual(search(path='/plone/news'),
                         ['/plone/news', '/plone/news/aggregator',
                          '/plone/news/folder'])
        self.assertEqual(search(path={'query': '/plone/news'}),
                         ['/plone/news', '/plone/news/aggregator',
                          '/plone/news/folder'])
        self.assertEqual(search(path={'query': '/plone/news', 'depth': -1}),
                         ['/plone/news', '/plone/news/aggregator',
                          '/plone/news/folder'])
        self.assertEqual(search(path={'query': '/plone/news', 'depth': 0}),
                         ['/plone/news'])

        expected = ['/plone/events',
                    '/plone/front-page',
                    '/plone/news']
        if not HAS_PAC:
            expected.insert(0, '/plone/Members')
        self.assertEqual(search(path={'query': '/plone', 'depth': 1}),
                         expected)

    def testMultiplePathSearches(self):
        self.maintenance.reindex()
        request = dict(SearchableText='[* TO *]')

        def search(path, **kw):
            results = solrSearchResults(request, path=dict(query=path, **kw))
            return sorted([r.path_string for r in results])

        # multiple paths with equal length...
        path = ['/plone/news', '/plone/events']
        self.assertEqual(search(path), ['/plone/events',
                                        '/plone/events/aggregator',
                                        '/plone/news',
                                        '/plone/news/aggregator',
                                        '/plone/news/folder'])
        self.assertEqual(search(path, depth=-1), ['/plone/events',
                                                  '/plone/events/aggregator',
                                                  '/plone/news',
                                                  '/plone/news/aggregator',
                                                  '/plone/news/folder'])
        self.assertEqual(search(path, depth=0), ['/plone/events',
                                                 '/plone/news'])
        # depth 1 doesn't return level 0 objs, see ZCatalog
        self.assertEqual(search(path, depth=1), ['/plone/events/aggregator',
                                                 '/plone/news/aggregator',
                                                 '/plone/news/folder'])
        # multiple paths with different length...
        path = ['/plone/news', '/plone/events/aggregator']
        self.assertEqual(search(path), ['/plone/events/aggregator',
                                        '/plone/news',
                                        '/plone/news/aggregator',
                                        '/plone/news/folder'])
        self.assertEqual(search(path, depth=-1), ['/plone/events/aggregator',
                                                  '/plone/news',
                                                  '/plone/news/aggregator',
                                                  '/plone/news/folder'])
        self.assertEqual(search(path, depth=0), ['/plone/events/aggregator',
                                                 '/plone/news'])
        # depth 1 doesn't return level 0 objs, see ZCatalog
        self.assertEqual(search(path, depth=1), ['/plone/news/aggregator',
                                                 '/plone/news/folder'])
        expected = ['/plone/events',
                    '/plone/front-page',
                    '/plone/news',
                    '/plone/news/aggregator',
                    '/plone/news/folder']
        if not HAS_PAC:
            expected.insert(0, '/plone/Members')
        self.assertEqual(search(['/plone/news',
                                 '/plone'],
                                depth=1), expected)

    def testLogicalOperators(self):
        self.portal.news.setSubject(['News'])
        self.portal.events.setSubject(['Events'])
        self.portal['front-page'].setSubject(['News', 'Events'])
        self.maintenance.reindex()
        request = dict(SearchableText='[* TO *]')
        search = lambda subject: sorted([r.path_string for r in
                                         solrSearchResults(request,
                                                           Subject=subject)])
        self.assertEqual(search(dict(operator='and',
                                     query=['News'])),
                         ['/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='or', query=['News'])),
                         ['/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='or', query=['News', 'Events'])),
                         ['/plone/events', '/plone/front-page', '/plone/news'])
        self.assertEqual(search(dict(operator='and', query=['News',
                                                            'Events'])),
                         ['/plone/front-page'])

    def testBooleanValues(self):
        self.maintenance.reindex()
        request = dict(SearchableText='[* TO *]')
        results = solrSearchResults(request, is_folderish=True)
        self.assertEqual(len(results), len(DEFAULT_OBJS)-3)
        self.assertFalse('/plone/front-page' in [r.path_string
                                                 for r in results])
        results = solrSearchResults(request, is_folderish=False)
        self.assertEqual(sorted([r.path_string for r in results]),
                         ['/plone/events/aggregator',
                          '/plone/front-page',
                          '/plone/news/aggregator'])

    def testSearchSecurity(self):
        wf_tool = api.portal.get_tool('portal_workflow')
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        wfAction = wf_tool.doActionFor
        wf_tool.setChainForPortalTypes(('Folder', 'Collection'),
                                       'simple_publication_workflow')
        if HAS_PAC:
            wfAction(self.portal.news, 'retract')
            wfAction(self.portal.news.folder, 'retract')
            wfAction(self.portal.events, 'retract')
        wfAction(self.portal.news.aggregator, 'retract')
        wfAction(self.portal.events.aggregator, 'retract')
        wf_tool.updateRoleMappings()
        self.maintenance.reindex()
        request = dict(SearchableText='[* TO *]')
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), len(DEFAULT_OBJS))
        setRoles(self.portal, TEST_USER_ID, [])
        results = self.portal.portal_catalog(request)
        expected = ['/plone/front-page']
        if not HAS_PAC:
            expected.insert(0, '/plone/Members')
            expected.insert(1, '/plone/Members/' + TEST_USER_ID)
        self.assertEqual(sorted([r.path_string for r in results]), expected)

    def testEffectiveRange(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.news.setEffectiveDate(DateTime() + 1)
        self.portal.events.setExpirationDate(DateTime() - 1)
        self.maintenance.reindex()
        request = dict(SearchableText='[* TO *]')
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), len(DEFAULT_OBJS))
        setRoles(self.portal, TEST_USER_ID, [])
        results = self.portal.portal_catalog(request)
        self.assertEqual(len(results), len(DEFAULT_OBJS)-2)
        paths = [r.path_string for r in results]
        self.assertFalse('/plone/news' in paths)
        self.assertFalse('/plone/events' in paths)
        results = self.portal.portal_catalog(request, show_inactive=True)
        self.assertEqual(len(results), len(DEFAULT_OBJS))
        paths = [r.path_string for r in results]
        self.assertTrue('/plone/news' in paths)
        self.assertTrue('/plone/events' in paths)

    def testEffectiveRangeWithSteps(self):
        # set some content to become effective/expire around this time...
        now = DateTime('2010/09/09 15:21:08 UTC')
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.news.setEffectiveDate('2010/09/09 15:20:13 UTC')
        self.portal.events.setExpirationDate('2010/09/09 15:18:09 UTC')
        self.maintenance.reindex()
        # first test with the default step of 1 seconds, i.e. unaltered
        # we prevent having `effectiveRange` set, but pass an explicit value
        # the news item is already effective, the event expired...
        request = dict(use_solr=True, show_inactive=True, effectiveRange=now)
        results = self.portal.portal_catalog(request)
        paths = [r.path_string for r in results]
        self.assertTrue('/plone/news' in paths)
        self.assertFalse('/plone/events' in paths)
        self.assertEqual(len(results), len(DEFAULT_OBJS)-1)
        # with a granularity of 5 minutes the news item isn't effective yet
        self.config.effective_steps = 300
        results = self.portal.portal_catalog(request)
        paths = [r.path_string for r in results]
        self.assertFalse('/plone/news' in paths)
        self.assertFalse('/plone/events' in paths)
        self.assertEqual(len(results), len(DEFAULT_OBJS)-2)
        # with 15 minutes the event hasn't expired yet, though
        self.config.effective_steps = 900
        results = self.portal.portal_catalog(request)
        paths = [r.path_string for r in results]
        self.assertFalse('/plone/news' in paths)
        self.assertTrue('/plone/events' in paths)
        self.assertEqual(len(results), len(DEFAULT_OBJS)-1)

    def testNoAutoCommitIndexing(self):
        connection = getUtility(ISolrConnectionManager).getConnection()
        self.config.auto_commit = False        # disable committing
        set_attributes(self.folder, values={'title': 'Foo'})
        commit()
        # no indexing happens, make sure we give the server some time
        sleep(4)
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0)

    def testCommitWithinIndexing(self):
        connection = getUtility(ISolrConnectionManager).getConnection()
        self.config.commit_within = 1000
        self.portal.invokeFactory('Folder', id='foo', title='Foo')
        commit()
        # no indexing happens
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0)
        # but after some time, results are there
        sleep(4.0)
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)

    def testLimitSearchResults(self):
        self.maintenance.reindex()
        results = self.search('+path_parents:\/plone').results()
        self.assertEqual(results.numFound, str(len(DEFAULT_OBJS)))
        self.assertEqual(len(results), len(DEFAULT_OBJS))
        # now let's limit the returned results
        config = getConfig()
        config.max_results = 2
        results = self.search('+path_parents:\/plone').results()
        self.assertEqual(results.numFound, str(len(DEFAULT_OBJS)))
        self.assertEqual(len(results), 2)
        # an explicit value should still override things
        results = self.search('+path_parents:\/plone', rows=5).results()
        self.assertEqual(results.numFound, str(len(DEFAULT_OBJS)))
        self.assertEqual(len(results), 5)

    def testSortParameters(self):
        self.maintenance.reindex()

        search = lambda attr, **kw: [getattr(r, attr, '?')
                                     for r in
                                     solrSearchResults(
                                         request=dict(
                                             SearchableText='[* TO *]',
                                             path=dict(query='/plone',
                                                       depth=1)), **kw)]
        first_level_objs = [i for i in DEFAULT_OBJS if i['depth'] == 0]
        self.assertEqual(search('Title', sort_on='Title'),
                         sorted([i['Title'] for i in first_level_objs]))
        self.assertEqual(search('Title', sort_on='Title',
                                sort_order='reverse'),
                         sorted([i['Title']
                                 for i in first_level_objs], reverse=True))
        required = [i['getId'] for i in sorted(first_level_objs,
                                               key=itemgetter('Title'),
                                               reverse=True)]
        self.assertEqual(search('getId', sort_on='Title',
                                sort_order='descending'), required)
        self.assertEqual(search('Title', sort_on='Title', sort_limit=4),
                         sorted([i['Title']
                                 for i in first_level_objs])[:4]
                         + ['?' for i in range(len(first_level_objs) - 4)])
        self.assertEqual(search('Title',
                                sort_on='Title',
                                sort_order='reverse',
                                sort_limit='3'),
                         sorted([i['Title']
                                 for i in first_level_objs],
                                reverse=True)[:3] +
                         ['?' for i in range(len(first_level_objs) - 3)])
        # test sort index aliases
        schema = self.search.getManager().getSchema()
        self.assertFalse('sortable_title' in schema)
        self.assertEqual(search('Title', sort_on='sortable_title'),
                         sorted([i['Title'] for i in first_level_objs]))
        # also make sure a non-existing sort index doesn't break things
        self.assertFalse('foo' in schema)
        self.assertEqual(len(search('Title', sort_on='foo')),
                         len(first_level_objs))

    def testFlareHelpers(self):
        self.portal.invokeFactory('Folder', id='foo', title='Foo')
        folder = self.portal.foo
        commit()                        # indexing happens on commit
        results = solrSearchResults(SearchableText='Foo')
        self.assertEqual(len(results), 1)
        flare = results[0]
        path = '/'.join(folder.getPhysicalPath())
        self.assertEqual(flare.Title, 'Foo')
        self.assertEqual(flare.getObject(), folder)
        self.assertEqual(flare.getPath(), path)
        self.assertTrue(flare.getURL().startswith('http://'))
        self.assertEqual(flare.getURL(), folder.absolute_url())
        self.assertTrue(flare.getURL(relative=True).startswith('/'))
        self.assertEqual(flare.getURL(relative=True), path)
        self.assertTrue(flare.getURL().endswith(flare.getURL(relative=True)))
        self.assertEqual(flare.getId, folder.getId())
        self.assertEqual(flare.id, folder.getId())

    def testWildcardSearches(self):
        self.maintenance.reindex()
        self.portal.invokeFactory('Document', id='newbie', title='Newbie!')
        results = solrSearchResults(SearchableText='New*')
        self.assertEqual(len(results), 2)
        commit()                        # indexing happens on commit
        results = solrSearchResults(SearchableText='New*')
        self.assertEqual(len(results), 3)
        self.assertEqual(sorted([i.Title for i in results]),
                         ['Newbie!', 'News', 'NewsFolder'])
        # wildcard searches can also be applied to other indexes...
        self.config.required = []
        results = solrSearchResults(Title='New*')
        self.assertEqual(len(results), 3)
        self.assertEqual(sorted([i.Title for i in results]),
                         ['Newbie!', 'News', 'NewsFolder'])
        # ...but don't work on non-text fields
        results = solrSearchResults(Type='D*')
        self.assertEqual(len(results), 0)

    def testWildcardSearchesMultipleWords(self):
        self.maintenance.reindex()
        self.portal.invokeFactory('Document', id='bg', title='Brazil Germany')
        commit()                        # indexing happens on commit
        results = solrSearchResults(SearchableText='Braz*')
        self.assertEqual(len(results), 1)
        results = solrSearchResults(SearchableText='Brazil Germa*')
        self.assertEqual(len(results), 1)

    def testWildcardSearchesUnicode(self):
        self.maintenance.reindex()
        self.portal.invokeFactory('Document', id='an', title=u'Ärger nøkkel')
        commit()
        results = solrSearchResults(SearchableText=u'Ärger')
        self.assertEqual(len(results), 1)
        results = solrSearchResults(SearchableText=u'Ärg*')
        self.assertEqual(len(results), 1)
        results = solrSearchResults(SearchableText=u'nøkkel')
        self.assertEqual(len(results), 1)
        results = solrSearchResults(SearchableText=u'nø*')
        self.assertEqual(len(results), 1)

    def testAbortedTransaction(self):
        connection = getUtility(ISolrConnectionManager).getConnection()
        # we cannot use `commit` here, since the transaction should get
        # aborted, so let's make sure processing the queue directly works...
        self.portal.invokeFactory('Folder', id='foo', title='Foo')
        processQueue()
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 0)
        getQueue().commit()
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)
        # now let's test aborting, but make sure there's nothing left in
        # the queue (by calling `commit`)
        set_attributes(self.folder, values={'title': 'Bar'})
        processQueue()
        result = connection.search(q='+Title:Bar').read()
        self.assertEqual(numFound(result), 0)
        getQueue().abort()
        commit()
        result = connection.search(q='+Title:Bar').read()
        self.assertEqual(numFound(result), 0)
        # the old title should still be exist...
        result = connection.search(q='+Title:Foo').read()
        self.assertEqual(numFound(result), 1)

    def testTimeoutResetAfterSearch(self):
        self.config.search_timeout = 1.0      # specify the timeout
        connection = getUtility(ISolrConnectionManager).getConnection()
        self.assertEqual(connection.conn.sock.gettimeout(), None)
        results = self.search('+Title:Foo').results()
        self.assertEqual(results.numFound, '0')
        self.assertEqual(connection.conn.sock.gettimeout(), None)

    def testEmptyStringSearch(self):
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText=' ', path='/plone')
        self.assertEqual(len(results), len(DEFAULT_OBJS))

    def testSearchableTopic(self):
        self.maintenance.reindex()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder.invokeFactory('Collection', id='news', title='some news')
        news = self.folder.news
        news.setQuery([{'i': 'SearchableText',
                        'o': 'plone.app.querystring.operation.string.contains',
                        'v': 'News'}])
        results = news.queryCatalog()
        self.assertEqual(sorted([
            (callable(r.Title) and r.Title() or r.Title, r.getPath())
            for r in results]),
            [('News', '/plone/news/aggregator'),
             ('NewsFolder', '/plone/news')])

    def testSearchDateRange(self):
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='News',
                                    created=dict(query=DateTime('1970/02/01'),
                                                 range='min'))
        self.assertEqual(len(results), 2)

    def testSolrIndexesVocabulary(self):
        vocab = getUtility(IVocabularyFactory, name='collective.solr.indexes')
        indexes = [i.token for i in vocab(self.portal)]
        self.assertTrue('SearchableText' in indexes)
        self.assertTrue('path_depth' in indexes)
        self.assertFalse('path_string' in indexes)

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
        results = solrSearchResults(request, portal_type='Collection')
        self.assertEqual([(r.Title, r.path_string) for r in results],
                         [('News', '/plone/news/aggregator')])
        self.assertEqual(len(log), 1)
        self.assertEqual(log[-1][1]['fq'], ['+portal_type:Collection'], log)
        # let's test again with an already existing filter query parameter
        request = dict(SearchableText='News', fq='+review_state:published')
        results = solrSearchResults(request, portal_type='Collection')
        self.assertEqual([(r.Title, r.path_string) for r in results],
                         [('News', '/plone/news/aggregator')])
        self.assertEqual(len(log), 2)
        self.assertEqual(sorted(log[-1][1]['fq']),
                         ['+portal_type:Collection',
                          '+review_state:published'], log)
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
        # test again with `&&` and `||` aliases
        request = dict(SearchableText='Bar || Foo')
        results = solrSearchResults(request)
        self.assertEqual(len(results), 3)
        request = dict(SearchableText='Bar && Foo')
        results = solrSearchResults(request)
        self.assertEqual(len(results), 1)

    def testMultiValueSearch(self):
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.portal.invokeFactory('Event', id='event1', title='Welcome')
        self.maintenance.reindex()
        results = solrSearchResults(SearchableText='Welcome',
                                    portal_type=['Event', 'Document'])
        self.assertEqual(len(results), 2)
        self.assertEqual(sorted([r.path_string for r in results]),
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
        config = getConfig()
        config.required = []
        config.filter_queries = [u'portal_type', u'Language']
        results = solrSearchResults(portal_type=['Document'])
        paths = [p.path_string for p in results]
        self.assertTrue('/plone/front-page' in paths)

    def testAccessSearchResultsFromPythonScript(self):
        self.maintenance.reindex()
        from Products.PythonScripts.PythonScript import manage_addPythonScript
        manage_addPythonScript(self.folder, 'foo')
        self.folder.foo.write('return [r.Title for r in '
                              'context.portal_catalog(SearchableText="News")]')
        self.assertEqual(self.folder.foo(), ['News', 'NewsFolder'])

    def testSearchForTermWithHyphen(self):
        self.portal.invokeFactory('Document', id='fb', title='foo-bar')
        commit()
        results = solrSearchResults(SearchableText='foo')
        self.assertEqual(sorted([r.Title for r in results]), ['foo-bar'])
        results = solrSearchResults(SearchableText='foo-bar')
        self.assertEqual(sorted([r.Title for r in results]), ['foo-bar'])
        results = solrSearchResults(SearchableText='bar')
        self.assertEqual(sorted([r.Title for r in results]), ['foo-bar'])
        # second round
        self.portal.invokeFactory('Document', id='fb2', title='2010-123')
        commit()
        results = solrSearchResults(SearchableText='2010-123')
        self.assertEqual(sorted([r.Title for r in results]), ['2010-123'])
        results = solrSearchResults(SearchableText='2010:123')
        self.assertEqual(sorted([r.Title for r in results]), ['2010-123'])
        results = solrSearchResults(SearchableText='2010')
        self.assertEqual(sorted([r.Title for r in results]), ['2010-123'])
        results = solrSearchResults(SearchableText='123')
        self.assertEqual(sorted([r.Title for r in results]), ['2010-123'])

    def testSearchForTermWithColon(self):
        self.portal.invokeFactory('Folder', id='tmc', title='foo:bar')
        commit()
        results = solrSearchResults(SearchableText='foo')
        self.assertEqual(sorted([r.Title for r in results]), ['foo:bar'])
        results = solrSearchResults(SearchableText='foo')
        self.assertEqual(sorted([r.Title for r in results]), ['foo:bar'])
        results = solrSearchResults(SearchableText='bar')
        self.assertEqual(sorted([r.Title for r in results]), ['foo:bar'])
        # second round
        self.portal.invokeFactory('Folder', id='tmp2', title=u'2010:ändern')
        commit()
        results = solrSearchResults(SearchableText='2010')
        self.assertEqual(sorted([r.Title for r in results]), [u'2010:ändern'])
        results = solrSearchResults(SearchableText=u'2010:ändern')
        self.assertEqual(sorted([r.Title for r in results]), [u'2010:ändern'])
        results = solrSearchResults(SearchableText=u'andern')
        self.assertEqual(sorted([r.Title for r in results]), [u'2010:ändern'])

    def testSearchForTermWithForwardSlash(self):
        self.portal.invokeFactory('Document', id='fsb', title='foo/bar')
        commit()
        results = solrSearchResults(SearchableText='foo')
        self.assertEqual(sorted([r.Title for r in results]), ['foo/bar'])
        results = solrSearchResults(SearchableText='foo/')
        self.assertEqual(sorted([r.Title for r in results]), ['foo/bar'])
        results = solrSearchResults(SearchableText='foo/bar')
        self.assertEqual(sorted([r.Title for r in results]), ['foo/bar'])
        results = solrSearchResults(SearchableText='/bar')
        self.assertEqual(sorted([r.Title for r in results]), ['foo/bar'])
        results = solrSearchResults(SearchableText='bar')
        self.assertEqual(sorted([r.Title for r in results]), ['foo/bar'])
        results = solrSearchResults(SearchableText='(foo/ AND bar)')
        self.assertEqual(sorted([r.Title for r in results]), ['foo/bar'])
        results = solrSearchResults(SearchableText='(foo/ OR boo)')
        self.assertEqual(sorted([r.Title for r in results]), ['foo/bar'])

    def testBatchedSearchResults(self):
        self.portal.invokeFactory('Document', id='one', title='Aaa A')
        self.portal.invokeFactory('Document', id='two', title='Aaa B')
        self.portal.invokeFactory('Document', id='three', title='Aaa C')
        self.maintenance.reindex()
        search = lambda **kw: [getattr(i, 'Title', None) for i in
                               solrSearchResults(SearchableText='A*',
                                                 portal_type='Document',
                                                 sort_on='Title', **kw)]
        self.assertEqual(search(),
                         ['Aaa A', 'Aaa B', 'Aaa C'])
        # when a batch size is given, the length should remain the same,
        # but only items in the batch actually exist...
        self.assertEqual(search(b_size=2),
                         ['Aaa A', 'Aaa B', None])
        # given a start value, the batch is moved within the search results
        self.assertEqual(search(b_size=2, b_start=1),
                         [None, 'Aaa B', 'Aaa C'])

    def testGetObjectOnPrivateObject(self):
        self.maintenance.reindex()
        acl_users = getToolByName(self.portal, 'acl_users')
        acl_users.userFolderAddUser('user1', 'secret', ['Manager'], [])
        login(self.portal, 'user1')
        self.portal.invokeFactory('Document', id='doc', title='Foo')
        login(self.portal, TEST_USER_NAME)
        commit()                        # indexing happens on commit
        setRoles(self.portal, TEST_USER_ID, [''])
        results = solrSearchResults(SearchableText='Foo')
        self.assertEqual(len(results), 1)
        self.assertRaises(Unauthorized, results[0].getObject)

    def testExcludeUserFromAllowedRolesAndUsers(self):
        login(self.portal, 'user1')
        self.portal.invokeFactory('Document', id='doc', title='Foo')
        login(self.portal, TEST_USER_NAME)
        self.maintenance.reindex()
        # first test the default of not removing the user
        results = self.portal.portal_catalog(use_solr=True)
        self.assertEqual(len(results), len(DEFAULT_OBJS)+1)
        paths = [r.path_string for r in results]
        self.assertTrue('/plone/doc' in paths)
        # now we have it removed...
        self.config.exclude_user = True
        setRoles(self.portal, TEST_USER_ID, [])
        results = self.portal.portal_catalog(use_solr=True)
        self.assertEqual(len(results), len(DEFAULT_OBJS))
        paths = [r.path_string for r in results]
        self.assertFalse('/plone/doc' in paths)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        del self.portal['doc']

    def testCleanup_removed(self):
        self.maintenance.reindex()
        # low level delete to force ascync index and
        self.portal._delOb('news')
        resp = self.search('NewsFolder')
        self.assertEqual(len(resp), 1)
        pf = PloneFlare(resp.results()[0])
        self.assertEqual(pf.getObject(), None)
        self.maintenance.cleanup()
        resp = self.search('NewsFolder')
        # NewsFolder was removed from index too
        self.assertEqual(len(resp), 0)

    def testCleanup_uid(self):
        self.maintenance.reindex()
        # low level delete to force ascync index and
        from Products.Archetypes.config import UUID_ATTR
        from plone.uuid.interfaces import ATTRIBUTE_NAME
        from plone.uuid.interfaces import IUUID
        uuid_orig = IUUID(self.portal['news'])

        # Dexterity
        setattr(self.portal['news'], ATTRIBUTE_NAME, 'test-solr-uid')
        # Archetypes
        setattr(self.portal['news'], UUID_ATTR, 'test-solr-uid')
        resp = self.search('NewsFolder')
        self.assertEqual(len(resp), 1)
        self.assertEqual(resp.results()[0]['UID'], uuid_orig)
        self.maintenance.cleanup()
        resp = self.search('NewsFolder')
        # NewsFolder was removed from index too
        self.assertEqual(resp.results()[0]['UID'], 'test-solr-uid')

    def testOptimize(self):
        """ Test call to optimze works

            There is nothing more to check
        """
        self.maintenance.reindex()
        self.maintenance.optimize()
        self.assertTrue(True)
