# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName

try:
    from Products.CMFCore.interfaces import IIndexQueueProcessor
except ImportError:
    # Plone < 5.1
    from collective.indexing.interfaces import IIndexQueueProcessor
from collective.solr.exceptions import SolrInactiveException
from collective.solr.interfaces import ISearch
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.interfaces import IZCMLSolrConnectionConfig
from collective.solr.mangler import mangleQuery
from collective.solr.testing import HAS_PAC
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from collective.solr.tests.utils import fakehttp
from collective.solr.tests.utils import getData
from collective.solr.utils import getConfig
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles

# from socket import error
# from socket import timeout
# from time import sleep
from transaction import commit
from unittest import TestCase
from zope.component import getGlobalSiteManager
from zope.component import getUtilitiesFor
from zope.component import queryUtility
from zope.configuration import xmlconfig
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

import unittest


class UtilityTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def testGenericInterface(self):
        proc = queryUtility(IIndexQueueProcessor, name="solr")
        self.assertTrue(proc, "utility not found")
        self.assertTrue(IIndexQueueProcessor.providedBy(proc))
        self.assertTrue(ISolrIndexQueueProcessor.providedBy(proc))

    def testSolrInterface(self):
        proc = queryUtility(ISolrIndexQueueProcessor, name="solr")
        self.assertTrue(proc, "utility not found")
        self.assertTrue(IIndexQueueProcessor.providedBy(proc))
        self.assertTrue(ISolrIndexQueueProcessor.providedBy(proc))

    def testRegisteredProcessors(self):
        procs = list(getUtilitiesFor(IIndexQueueProcessor))
        self.assertTrue(procs, "no utilities found")
        solr = queryUtility(ISolrIndexQueueProcessor, name="solr")
        self.assertTrue(
            solr in [util for name, util in procs], "solr utility not found"
        )

    def testSearchInterface(self):
        search = queryUtility(ISearch)
        self.assertTrue(search, "search utility not found")
        self.assertTrue(ISearch.providedBy(search))


class QueryManglerTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def testExcludeUserFromAllowedRolesAndUsers(self):
        config = getConfig()
        search = queryUtility(ISearch)
        schema = search.getManager().getSchema() or {}
        # first test the default setting, i.e. not removing the user
        keywords = dict(allowedRolesAndUsers=["Member", "user$test_user_1_"])
        mangleQuery(keywords, config, schema)
        self.assertEqual(
            keywords, {"allowedRolesAndUsers": ["Member", "user$test_user_1_"]}
        )
        # now let's remove it...
        config.exclude_user = True
        keywords = dict(allowedRolesAndUsers=["Member", "user$test_user_1_"])
        mangleQuery(keywords, config, schema)
        self.assertEqual(keywords, {"allowedRolesAndUsers": ["Member"]})


class IndexingTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        replies = (
            getData("plone_schema.xml"),
            getData("add_response.txt"),
            getData("add_response.txt"),
            getData("add_response.txt"),
            getData("commit_response.txt"),
        )
        self.proc = queryUtility(ISolrConnectionManager)
        self.proc.setHost(active=True)
        conn = self.proc.getConnection()
        fakehttp(conn, *replies)  # fake schema response
        self.proc.getSchema()  # read and cache the schema
        self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Folder", id="folder")
        self.folder = self.portal.folder
        commit()

    def tearDown(self):
        self.proc.closeConnection(clearSchema=True)
        # due to the `commit()` in the tests below the activation of the
        # solr support in `afterSetUp` needs to be explicitly reversed...
        self.proc.setHost(active=False)
        commit()

    def testIndexObject(self):
        output = []
        connection = self.proc.getConnection()
        connection.get_schema()  # cache schema to avoid multiple calls

        responses = (getData("plone_schema.xml"), getData("commit_response.txt"))
        output = fakehttp(connection, *responses)  # fake responses
        self.folder.title = "Foo"
        self.portal.invokeFactory("Folder", id="myfolder", title="Foo")
        self.assertEqual(str(output), "", "reindexed unqueued!")
        commit()  # indexing happens on commit
        required = '<field name="Title" update="set">Foo</field>'
        self.assertTrue(str(output).find(required) > 0, '"title" data not found')

    def testNoIndexingForNonCatalogAwareContent(self):
        output = []
        connection = self.proc.getConnection()
        responses = [getData("dummy_response.txt")] * 42  # set up enough...
        output = fakehttp(connection, *responses)  # fake responses
        notify(ObjectModifiedEvent(self.folder))
        self.portal.invokeFactory("Folder", id="myfolder", title="Foo")
        commit()  # indexing happens on commit
        self.assertNotEqual(repr(output).find("Foo"), -1, "title not found")
        self.assertEqual(
            repr(output).find("at_references"), -1, "`at_references` found?"
        )


class SiteSearchTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    def tearDown(self):
        # resetting the solr configuration after each test isn't strictly
        # needed at the moment, but it triggers the `ConnectionStateError`
        # when the other tests (in `errors.txt`) is trying to perform an
        # actual solr search...
        queryUtility(ISolrConnectionManager).setHost(active=False)

    def testInactiveException(self):
        search = queryUtility(ISearch)
        self.assertRaises(SolrInactiveException, search, "foo")


#    def testSearchWithoutServer(self):
#        config = getConfig()
#        config.active = True
#        config.port = 55555     # random port so the real solr might still run
#        search = queryUtility(ISearch)
#        self.assertRaises(error, search, 'foo')

#   Why should this raise a socket error?
#    def testSearchWithoutSearchableTextInPortalCatalog(self):
#        config = queryUtility(ISolrConnectionConfig)
#        config.active = True
#        config.port = 55555     # random port so the real solr might still run
#        catalog = self.portal.portal_catalog
#        catalog.delIndex('SearchableText')
#        self.assertFalse('SearchableText' in catalog.indexes())
#        query = self.portal.restrictedTraverse('queryCatalog')
#        request = dict(SearchableText='foo')
#        self.assertRaises(error, query, request)
#
# XXX: Enabling this test leads to a test deadlock. Needs to be investigated.
# (timo)
#    def testSearchTimeout(self):
#        config = getConfig()
#        config.active = True
#        config.search_timeout = 2.0  # specify the timeout
#        config.port = 55555         # don't let the real solr disturb us
#
#        def quick(handler):         # set up fake http response
#            sleep(0.5)              # and wait a bit before sending it
#            handler.send_response(200, getData('search_response.txt'))
#
#        def slow(handler):          # set up another http response
#            sleep(3)                # but wait longer before sending it
#            handler.send_response(200, getData('search_response.txt'))
#        # We need a third handler, as the second one will timeout, which causes  # noqa
#        # the SolrConnection.doPost method to catch it and try to reconnect.
#        thread = fakeServer([quick, slow, slow], port=55555)
#        search = queryUtility(ISearch)
#        search('foo')               # the first search should succeed
#        try:
#            self.assertRaises(timeout, search, 'foo')   # but not the second
#        finally:
#            thread.join()           # the server thread must always be joined


class ZCMLSetupTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def tearDown(self):
        manager = queryUtility(ISolrConnectionManager)
        manager.setHost(active=False)
        zcmlconfig = queryUtility(IZCMLSolrConnectionConfig)
        gsm = getGlobalSiteManager()
        gsm.unregisterUtility(zcmlconfig, IZCMLSolrConnectionConfig)

    def testConnectionConfigurationViaZCML(self):
        import collective.solr

        context = xmlconfig.file("meta.zcml", collective.solr)
        xmlconfig.string(
            """
            <configure xmlns:solr="http://namespaces.plone.org/solr">
                <solr:connection host="127.0.0.23" port="3898" base="/foo" />
            </configure>
        """,
            context=context,
        )
        manager = queryUtility(ISolrConnectionManager)
        manager.setHost(active=True)  # also clears connection cache
        connection = manager.getConnection()
        self.assertEqual(connection.host, "127.0.0.23:3898")
        self.assertEqual(connection.solrBase, "/foo")


class SiteSetupTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]

    @unittest.skipIf(HAS_PAC, "Plone 4 Only")
    def testBrowserResourcesPlone4(self):
        cssreg = getToolByName(self.portal, "portal_css")
        self.assertTrue(
            cssreg.getResource(
                "++resource++collective.solr.resources/style.css"
            ).getEnabled()
        )

    def testTranslation(self):
        utrans = getToolByName(self.portal, "translation_service").utranslate

        def translate(msg):
            return utrans(msgid=msg, domain="solr")

        self.assertEqual(translate("portal_type"), u"Content type")
