# -*- coding: UTF-8 -*-
from collective.solr.interfaces import ISolrConnectionConfig
from zope.component import getUtility
from collective.solr.testing import \
    COLLECTIVE_SOLR_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID

import unittest2 as unittest


class SolrConnectionConfigIntegrationTest(unittest.TestCase):

    layer = COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.request['ACTUAL_URL'] = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_config(self):
        config = getUtility(ISolrConnectionConfig)
        self.assertEqual(config.active, False)
        self.assertEqual(config.host, '127.0.0.1')
        self.assertEqual(config.port, 8983)
        self.assertEqual(config.base, '/solr')
        self.assertEqual(config.async, False)
        self.assertEqual(config.auto_commit, True)
        self.assertEqual(config.commit_within, 0)
        self.assertEqual(config.index_timeout, 0.0)
        self.assertEqual(config.search_timeout, 0.0)
        self.assertEqual(config.max_results, 10000000)
        self.assertEqual(config.required, ('SearchableText',))
        self.assertEqual(
            config.search_pattern,
            "+(Title:{value}^5 OR Description:{value}^2 OR SearchableText:{value} OR SearchableText:({base_value}) OR searchwords:({base_value})^1000) +showinsearch:True")
        self.assertEqual(config.facets, ('portal_type', 'review_state'))
        self.assertEqual(config.filter_queries, ('portal_type',))
        self.assertEqual(config.slow_query_threshold, 0)
        self.assertEqual(config.effective_steps, 1)
        self.assertEqual(config.exclude_user, False)
        self.assertEqual(config.highlight_fields, ())
        self.assertEqual(config.highlight_formatter_pre, '[')
        self.assertEqual(config.highlight_formatter_post, ']')
        self.assertEqual(config.highlight_fragsize, 100)
        self.assertEqual(config.field_list, [])
