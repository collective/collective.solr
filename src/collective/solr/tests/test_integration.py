from unittest import defaultTestLoader
from collective.solr.tests.base import SolrTestCase

# test-specific imports go here...
from zope.component import queryUtility, getUtilitiesFor
from Products.CMFCore.utils import getToolByName
from collective.indexing.interfaces import IIndexQueueProcessor
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.interfaces import ISearch
from collective.solr.mangler import mangleQuery
from collective.solr.exceptions import SolrInactiveException
from collective.solr.tests.utils import getData, fakehttp, fakeServer
from transaction import commit
from socket import error, timeout
from time import sleep


class UtilityTests(SolrTestCase):

    def testGenericInterface(self):
        proc = queryUtility(IIndexQueueProcessor, name='solr')
        self.failUnless(proc, 'utility not found')
        self.failUnless(IIndexQueueProcessor.providedBy(proc))
        self.failUnless(ISolrIndexQueueProcessor.providedBy(proc))

    def testSolrInterface(self):
        proc = queryUtility(ISolrIndexQueueProcessor, name='solr')
        self.failUnless(proc, 'utility not found')
        self.failUnless(IIndexQueueProcessor.providedBy(proc))
        self.failUnless(ISolrIndexQueueProcessor.providedBy(proc))

    def testRegisteredProcessors(self):
        procs = list(getUtilitiesFor(IIndexQueueProcessor))
        self.failUnless(procs, 'no utilities found')
        solr = queryUtility(ISolrIndexQueueProcessor, name='solr')
        self.failUnless(solr in [util for name, util in procs],
            'solr utility not found')

    def testSearchInterface(self):
        search = queryUtility(ISearch)
        self.failUnless(search, 'search utility not found')
        self.failUnless(ISearch.providedBy(search))


class QueryManglerTests(SolrTestCase):

    def testExcludeUserFromAllowedRolesAndUsers(self):
        config = queryUtility(ISolrConnectionConfig)
        search = queryUtility(ISearch)
        schema = search.getManager().getSchema() or {}
        # first test the default setting, i.e. not removing the user
        keywords = dict(allowedRolesAndUsers=['Member', 'user$test_user_1_'])
        mangleQuery(keywords, config, schema)
        self.assertEqual(keywords, {
            'allowedRolesAndUsers': ['Member', 'user$test_user_1_'],
        })
        # now let's remove it...
        config.exclude_user = True
        keywords = dict(allowedRolesAndUsers=['Member', 'user$test_user_1_'])
        mangleQuery(keywords, config, schema)
        self.assertEqual(keywords, {
            'allowedRolesAndUsers': ['Member'],
        })


class IndexingTests(SolrTestCase):

    def afterSetUp(self):
        schema = getData('plone_schema.xml')
        self.proc = queryUtility(ISolrConnectionManager)
        self.proc.setHost(active=True)
        conn = self.proc.getConnection()
        fakehttp(conn, schema)              # fake schema response
        self.proc.getSchema()               # read and cache the schema
        self.folder.unmarkCreationFlag()    # stop LinguaPlone from renaming

    def beforeTearDown(self):
        self.proc.closeConnection(clearSchema=True)
        # due to the `commit()` in the tests below the activation of the
        # solr support in `afterSetUp` needs to be explicitly reversed...
        self.proc.setHost(active=False)
        commit()

    def testIndexObject(self):
        output = []
        connection = self.proc.getConnection()
        responses = getData('add_response.txt'), getData('commit_response.txt')
        output = fakehttp(connection, *responses)           # fake responses
        self.folder.processForm(values={'title': 'Foo'})    # updating sends
        self.assertEqual(self.folder.Title(), 'Foo')
        self.assertEqual(str(output), '', 'reindexed unqueued!')
        commit()                        # indexing happens on commit
        required = '<field name="Title">Foo</field>'
        self.assert_(str(output).find(required) > 0, '"title" data not found')

    def testNoIndexingWithMethodOverride(self):
        self.setRoles(['Manager'])
        output = []
        connection = self.proc.getConnection()
        responses = [getData('dummy_response.txt')] * 42
        output = fakehttp(connection, *responses)
        self.folder.invokeFactory('Topic', id='coll', title='a collection')
        self.folder.coll.addCriterion('Type', 'ATPortalTypeCriterion')
        self.assertTrue('crit__Type_ATPortalTypeCriterion' not in str(output))
        commit()
        self.assert_(repr(output).find('a collection') > 0,
            '"title" data not found')
        self.assert_(repr(output).find('crit') == -1, 'criterion indexed?')
        objs = self.portal.portal_catalog(portal_type='ATPortalTypeCriterion')
        self.assertEqual(list(objs), [])
        self.folder.manage_delObjects('coll')

    def testNoIndexingForNonCatalogAwareContent(self):
        self.setRoles(['Manager'])
        output = []
        connection = self.proc.getConnection()
        responses = [getData('dummy_response.txt')] * 42    # set up enough...
        output = fakehttp(connection, *responses)           # fake responses
        ref = self.folder.addReference(self.portal.news, 'referencing')
        self.folder.processForm(values={'title': 'Foo'})
        commit()                        # indexing happens on commit
        self.assertNotEqual(repr(output).find('Foo'), -1, 'title not found')
        self.assertEqual(repr(output).find(ref.UID()), -1, 'reference found?')
        self.assertEqual(repr(output).find('at_references'), -1,
            '`at_references` found?')


class SiteSearchTests(SolrTestCase):

    def beforeTearDown(self):
        # resetting the solr configuration after each test isn't strictly
        # needed at the moment, but it triggers the `ConnectionStateError`
        # when the other tests (in `errors.txt`) is trying to perform an
        # actual solr search...
        queryUtility(ISolrConnectionManager).setHost(active=False)

    def testSkinSetup(self):
        skins = self.portal.portal_skins.objectIds()
        self.failUnless('solr_site_search' in skins, 'no solr skin?')

    def testInactiveException(self):
        search = queryUtility(ISearch)
        self.assertRaises(SolrInactiveException, search, 'foo')

    def testSearchWithoutServer(self):
        config = queryUtility(ISolrConnectionConfig)
        config.active = True
        config.port = 55555     # random port so the real solr might still run
        search = queryUtility(ISearch)
        self.assertRaises(error, search, 'foo')

    def testSearchWithoutSearchableTextInPortalCatalog(self):
        config = queryUtility(ISolrConnectionConfig)
        config.active = True
        config.port = 55555     # random port so the real solr might still run
        catalog = self.portal.portal_catalog
        catalog.delIndex('SearchableText')
        self.failIf('SearchableText' in catalog.indexes())
        query = self.portal.restrictedTraverse('queryCatalog')
        request = dict(SearchableText='foo')
        self.assertRaises(error, query, request)

    def testSearchTimeout(self):
        config = queryUtility(ISolrConnectionConfig)
        config.active = True
        config.search_timeout = 2   # specify the timeout
        config.port = 55555         # don't let the real solr disturb us
        def quick(handler):         # set up fake http response
            sleep(0.5)              # and wait a bit before sending it
            handler.send_response(200, getData('search_response.txt'))
        def slow(handler):          # set up another http response
            sleep(3)                # but wait longer before sending it
            handler.send_response(200, getData('search_response.txt'))
        # We need a third handler, as the second one will timeout, which causes
        # the SolrConnection.doPost method to catch it and try to reconnect.
        thread = fakeServer([quick, slow, slow], port=55555)
        search = queryUtility(ISearch)
        search('foo')               # the first search should succeed
        try:
            self.assertRaises(timeout, search, 'foo')   # but not the second
        finally:
            thread.join()           # the server thread must always be joined

    def testSchemaUrlFallback(self):
        config = queryUtility(ISolrConnectionConfig)
        config.active = True
        config.port = 55555         # random port so the real solr can still run
        def notfound(handler):      # set up fake 404 response
            self.assertEqual(handler.path,
                '/solr/admin/file/?file=schema.xml')
            handler.send_response(404, getData('not_found.txt'))
        def solr12(handler):        # set up response with the schema
            self.assertEqual(handler.path,
                '/solr/admin/get-file.jsp?file=schema.xml')
            handler.send_response(200, getData('schema.xml'))
        responses = [notfound, solr12]
        thread = fakeServer(responses, config.port)
        schema = queryUtility(ISolrConnectionManager).getSchema()
        thread.join()               # the server thread must always be joined
        self.assertEqual(responses, [])
        self.assertEqual(len(schema), 21)   # 21 items defined in schema.xml


class SiteSetupTests(SolrTestCase):

    def testBrowserResources(self):
        registry = getToolByName(self.portal, 'portal_css')
        css = '++resource++collective.solr.resources/style.css'
        self.failUnless(css in registry.getResourceIds())

    def testTranslation(self):
        utrans = getToolByName(self.portal, 'translation_service').utranslate
        translate = lambda msg: utrans(msgid=msg, domain='solr')
        self.assertEqual(translate('portal_type'), u'Content type')


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
