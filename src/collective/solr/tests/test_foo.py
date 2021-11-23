# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_parent
from DateTime import DateTime
from Missing import MV
from Products.CMFCore.utils import getToolByName
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
from six.moves import range
from time import sleep
from transaction import abort
from transaction import commit
from unittest import TestCase
from zExceptions import Unauthorized
from zope.component import getUtility, queryAdapter
from zope.interface import implementer
from zope.schema.interfaces import IVocabularyFactory

try:
    from Products.Archetypes.interfaces import IBaseObject
except ImportError:
    IBaseObject = None
try:
    from Products.Archetypes.config import UUID_ATTR
except ImportError:
    UUID_ATTR = None

import unittest

from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.restapi.testing import RelativeSession


class SolrMaintenanceTests(unittest.TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        activateAndReindex(self.portal)
        import transaction

        transaction.commit()
        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def tearDown(self):
        activate(active=False)

    def test_foo(self):
        response = self.api_session.get("/@solr")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
