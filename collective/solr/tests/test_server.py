from unittest import makeSuite, defaultTestLoader
from zope.component import getUtility
from httplib import HTTPConnection
from socket import error
from re import search

from collective.solr.tests.base import SolrTestCase
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.utils import activate


class SolrMaintenanceTests(SolrTestCase):

    def afterSetUp(self):
        activate()

    def beforeTearDown(self):
        activate(active=False)

    def found(self, result):
        match = search(r'numFound="(\d+)"', result)
        if match is not None:
            match = int(match.group(1))
        return match

    def testClear(self):
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()
        # make sure nothing is indexed
        connection.deleteByQuery('[* TO *]')
        connection.commit()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(self.found(result), 0)
        # now add something...
        connection.add(UID='foo', Title='bar')
        connection.commit()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(self.found(result), 1)
        # and clear things again...
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.clear()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(self.found(result), 0)

    def testReindex(self):
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()
        # make sure nothing is indexed
        connection.deleteByQuery('[* TO *]')
        connection.commit()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(self.found(result), 0)
        # reindex and check again...
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        maintenance.reindex()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(self.found(result), 9)

    def testPartialReindex(self):
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()
        # make sure nothing is indexed
        connection.deleteByQuery('[* TO *]')
        connection.commit()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(self.found(result), 0)
        # reindex and check again...
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        maintenance = self.portal.unrestrictedTraverse('news/solr-maintenance')
        maintenance.reindex()
        result = connection.search(q='[* TO *]').read()
        self.assertEqual(self.found(result), 1)


def solrStatus():
    """ test if the solr server is available """
    conn = HTTPConnection('localhost', 8983)
    try:
        conn.request('GET', '/solr/admin/ping')
        response = conn.getresponse()
        return ''
    except error, e:
        return e


def test_suite():
    status = solrStatus()
    if status:
        print 'WARNING: solr tests could not be run: "%s".' % status
        return makeSuite()
    else:
        return defaultTestLoader.loadTestsFromName(__name__)

