# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName

from unittest import TestSuite, defaultTestLoader

from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.tests.utils import pingSolr
from collective.solr.tests.base import SolrTestCase
from collective.solr.dispatcher import solrSearchResults
from collective.solr.utils import activate
from plone.dexterity.fti import DexterityFTI
from plone.dexterity.content import Item
from zope.interface import implements
from zope.interface import Interface
from zope.component import getUtility
from zope import schema

import unittest2 as unittest


class ILocation(Interface):

    geolocation = schema.TextLine(
        title=u"Geo Location",
        description=u"",
        required=False,
    )


class Location(Item):
    implements(ILocation)


class SolrSpatialSearchTests(SolrTestCase):

    def afterSetUp(self):
        self._setUpGeolocationCatalogIndex()
        self._setUpLocationType()
        self._makeSearchableTextOptionalInSolrConfiguration()
        activate()
        self.portal.REQUEST.RESPONSE.write = lambda x: x    # ignore output
        self.maintenance = self.portal.unrestrictedTraverse('solr-maintenance')
        self.maintenance.clear()
        self.maintenance.reindex()
        self.setRoles(('Manager',))

    def beforeTearDown(self):
        activate(active=False)

    def _setUpLocationType(self):
        types_tool = getToolByName(self.portal, 'portal_types')
        fti = DexterityFTI('Location')
        fti.klass = 'collective.solr.tests.test_spatial.Location'
        types_tool._setObject('Location', fti)

    def _setUpGeolocationCatalogIndex(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        catalog.addIndex('geolocation', 'FieldIndex')

    def _makeSearchableTextOptionalInSolrConfiguration(self):
        config = getUtility(ISolrConnectionConfig)
        config.required = ()

    def testGeoSpatialSearchWithExactLocation(self):
        self.portal.invokeFactory('Location', id='location1', title='Loc 1')
        self.portal.location1.geolocation = '50.2,-7.1'
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            spatial='true',
            portal_type='Location',
            sfield='geolocation',
            fq='{!bbox}',
            pt='50.2,-7.1',
            d=0,
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ['/plone/location1']
        )

    def testGeoSpatialSearchWithNearbyLocation(self):
        self.portal.invokeFactory('Location', id='location1', title='Loc 1')
        self.portal.location1.geolocation = '50.2,-7.1'
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            spatial='true',
            fq='{!bbox}',
            sfield='geolocation',
            pt='50.3,-7.4',
            d=100,
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ['/plone/location1']
        )

    def testGeoSpatialSearchWithLocationOutsideTheSearchBox(self):
        self.portal.invokeFactory('Location', id='location1', title='Loc 1')
        self.portal.location1.geolocation = '50.2,-7.1'
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            spatial='true',
            fq='{!bbox}',
            sfield='geolocation',
            pt='80,123',
            d=0.2,
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            []
        )

    # sort='geodist() desc' allows us to sort geolocations by distance.
    # it seems that right now collective.solr filters that param entirely.
    @unittest.skip('Sorting is not working yet.')
    def testGeoSpatialSearchSortByDistance(self):
        self.portal.invokeFactory('Location', id='location1', title='Loc 1')
        self.portal.location1.geolocation = '50,1'
        self.portal.location1.reindexObject()
        self.portal.invokeFactory('Location', id='location2', title='Loc 2')
        self.portal.location2.geolocation = '60,1'
        self.portal.location2.reindexObject()
        self.maintenance.reindex()

        # Query: 52,1 | 50,1 (locaction1) < 60,1 (location2)
        results = solrSearchResults(
            spatial='true',
            fq='{!bbox}',
            sfield='geolocation',
            pt='52,1',
            d=100,
            sort='geodist() desc'
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ['/plone/location2', '/plone/location1']
        )

        # Query: 58,1 | 60,1 (locaction2) < 50,1 (location1)
        results = solrSearchResults(
            spatial='true',
            fq='{!bbox}',
            sfield='geolocation',
            pt='58,1',
            d=100,
            sort='geodist() asc'
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ['/plone/location1', '/plone/location2'],
        )


def test_suite():
    if pingSolr():
        return defaultTestLoader.loadTestsFromName(__name__)
    else:
        return TestSuite()
