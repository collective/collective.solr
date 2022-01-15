# -*- coding: utf-8 -*-

from collective.solr.dispatcher import solrSearchResults
from collective.solr.interfaces import ISearch
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.local import getLocal
from collective.solr.manager import SolrConnectionManager
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from collective.solr.testing import activateAndReindex
from collective.solr.utils import activate
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component import queryUtility

import unittest


class SolrMulticoreTests(unittest.TestCase):
    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def _close_connections(self, keys):
        for key in keys:
            key = key is not None and key or ""
            manager = getUtility(ISolrConnectionManager, name=key)
            manager.closeConnection(clearSchema=True)

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        activateAndReindex(self.portal)
        self._close_connections(keys=(None,))
        sm = getSiteManager()
        self._plone_manager = SolrConnectionManager()
        sm.registerUtility(self._plone_manager, ISolrConnectionManager, name="plone")
        self._foo_manager = SolrConnectionManager()
        sm.registerUtility(self._foo_manager, ISolrConnectionManager, name="foo")

    def tearDown(self):
        activate(active=False)
        self._close_connections((None, "plone", "foo"))
        sm = getSiteManager()
        sm.unregisterUtility(self._plone_manager, ISolrConnectionManager, name="plone")
        sm.unregisterUtility(self._foo_manager, ISolrConnectionManager, name="foo")

    def test_default_utility(self):
        manager = queryUtility(ISolrConnectionManager)
        # Default manager must not have a core parameter
        self.assertIsNone(manager.core)
        self.assertEqual("connection", manager.connection_key)
        self.assertEqual("schema", manager.schema_key)

    def test_named_utilities(self):
        default_manager = queryUtility(ISolrConnectionManager)
        default_conn = default_manager.getConnection()
        default_schema = default_manager.getSchema()

        plone_manager = queryUtility(ISolrConnectionManager, name="plone")
        plone_manager.setCore("plone")
        self.assertEqual("plone", plone_manager.core)
        self.assertEqual("connection_plone", plone_manager.connection_key)
        self.assertEqual("schema_plone", plone_manager.schema_key)

        plone_conn = plone_manager.getConnection()
        self.assertTrue(default_conn != plone_conn)
        self.assertEqual("/solr/plone", plone_conn.solrBase)

        plone_schema = plone_manager.getSchema()
        self.assertEqual(default_schema, plone_schema)

        foo_manager = queryUtility(ISolrConnectionManager, name="foo")
        foo_manager.setCore("foo")
        self.assertEqual("foo", foo_manager.core)
        self.assertEqual("connection_foo", foo_manager.connection_key)
        self.assertEqual("schema_foo", foo_manager.schema_key)

        foo_conn = foo_manager.getConnection()
        self.assertTrue(default_conn != foo_conn)
        self.assertEqual("/solr/foo", foo_conn.solrBase)

    def test_search_on_core(self):
        # Verify that connections does not exist before search
        self.assertIsNone(getLocal("connection"))
        self.assertIsNone(getLocal("connection_plone"))

        search = getUtility(ISearch, context=self.portal)
        results_core = search("+Title:*Welcome to Plone*", core="plone").results()
        self.assertEqual(1, len(results_core))
        self.assertIsNone(getLocal("connection"))
        self.assertIsNotNone(getLocal("connection_plone"))

        results_default = search("+Title:*Welcome to Plone*").results()
        self.assertEqual(1, len(results_default))

        # Verify connections and schemas
        default_conn = getLocal("connection")
        plone_conn = getLocal("connection_plone")
        self.assertTrue(default_conn != plone_conn)
        self.assertIsNotNone(default_conn)
        self.assertIsNotNone(plone_conn)

    def test_solr_search_result_with_core(self):
        # Verify that connections and schemas does not exist before search
        self.assertIsNone(getLocal("connection"))
        self.assertIsNone(getLocal("schema"))
        self.assertIsNone(getLocal("connection_plone"))
        self.assertIsNone(getLocal("schema_plone"))

        results = solrSearchResults(
            self.request, Title="Welcome to Plone", use_solr=True, core="plone"
        )
        self.assertEqual(1, len(results))

        # Verify that only concerned schemas and connections are now defined
        self.assertIsNone(getLocal("connection"))
        self.assertIsNone(getLocal("schema"))
        self.assertIsNotNone(getLocal("connection_plone"))
        self.assertIsNotNone(getLocal("schema_plone"))
