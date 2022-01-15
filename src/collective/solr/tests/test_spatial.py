import unittest

from collective.solr.dispatcher import solrSearchResults
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.testing import (
    LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING,
    activateAndReindex,
)
from collective.solr.utils import activate, getConfig
from plone.app.testing import TEST_USER_ID, setRoles
from plone.dexterity.content import Item
from plone.dexterity.fti import DexterityFTI
from Products.CMFCore.utils import getToolByName
from transaction import commit
from zope import schema
from zope.component import getUtility
from zope.interface import Interface, implementer


class ILocation(Interface):

    geolocation = schema.TextLine(
        title=u"Geo Location", description=u"", required=False
    )


@implementer(ILocation)
class Location(Item):
    """ """


class SolrSpatialSearchTests(unittest.TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self._setUpGeolocationCatalogIndex()
        self._setUpLocationType()
        setRoles(self.portal, TEST_USER_ID, ("Manager",))
        self.config = getConfig()
        self.config.required = []
        self.maintenance = self.portal.unrestrictedTraverse("solr-maintenance")
        commit()
        self.response = self.request.RESPONSE
        self.write = self.response.write
        self.response.write = lambda x: x  # temporarily ignore output
        activateAndReindex(self.portal)

    def tearDown(self):
        activate(active=False)
        self.response.write = self.write

    def _setUpLocationType(self):
        types_tool = getToolByName(self.portal, "portal_types")
        fti = DexterityFTI("Location")
        fti.klass = "collective.solr.tests.test_spatial.Location"
        types_tool._setObject("Location", fti)

    def _setUpGeolocationCatalogIndex(self):
        catalog = getToolByName(self.portal, "portal_catalog")
        catalog.addIndex("geolocation", "FieldIndex")

    def _makeSearchableTextOptionalInSolrConfiguration(self):
        config = getUtility(ISolrConnectionConfig)
        config.required = ()

    def testGeoSpatialTypeIsIndexed(self):
        self.portal.invokeFactory("Location", id="location1", title="Loc 1")
        self.portal.location1.geolocation = "50.2,-7.1"
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(portal_type="Location")
        self.assertEqual(sorted([r.path_string for r in results]), ["/plone/location1"])

    def testGeoSpatialFieldCanBeDeleted(self):
        self.portal.invokeFactory("Location", id="location1", title="Loc 1")
        self.portal.location1.geolocation = "50.2,-7.1"
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            portal_type="Location",
            sfield="geolocation",
            fq="{!geofilt}",
            pt="50.2,-7.1",
            d=0,
        )
        self.assertEqual(sorted([r.path_string for r in results]), ["/plone/location1"])
        self.portal.location1.geolocation = None
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            portal_type="Location",
            sfield="geolocation",
            fq="{!geofilt}",
            pt="50.2,-7.1",
            d=0,
        )
        self.assertEqual(list(results), [])
        results = solrSearchResults(portal_type="Location")
        from Missing import Missing

        self.assertEqual(sorted([r.path_string for r in results]), ["/plone/location1"])
        self.assertTrue(isinstance(results[0].geolocation, Missing))

    def testGeoSpatialFieldCanBeUpdated(self):
        self.portal.invokeFactory("Location", id="location1", title="Loc 1")
        self.portal.location1.geolocation = "50.2,-7.1"
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            portal_type="Location",
            sfield="geolocation",
            fq="{!geofilt}",
            pt="50.2,-7.1",
            d=0,
        )
        self.assertEqual(sorted([r.path_string for r in results]), ["/plone/location1"])
        self.portal.location1.geolocation = "10.1, -8.4"
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            portal_type="Location",
            sfield="geolocation",
            fq="{!geofilt}",
            pt="10.1, -8.4",
            d=0,
        )
        self.assertEqual(sorted([r.path_string for r in results]), ["/plone/location1"])

    def testGeoSpatialSearchWithExactLocation(self):
        self.portal.invokeFactory("Location", id="location1", title="Loc 1")
        self.portal.location1.geolocation = "50.2,-7.1"
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            portal_type="Location",
            sfield="geolocation",
            fq="{!geofilt}",
            pt="50.2,-7.1",
            d=0,
        )
        self.assertEqual(sorted([r.path_string for r in results]), ["/plone/location1"])

    def testGeoSpatialSearchWithNearbyLocation(self):
        self.portal.invokeFactory("Location", id="location1", title="Loc 1")
        self.portal.location1.geolocation = "50.2,-7.1"
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            portal_type="Location",
            fq="{!geofilt}",
            sfield="geolocation",
            pt="50.3,-7.4",
            d=100,
        )
        self.assertEqual(sorted([r.path_string for r in results]), ["/plone/location1"])

    def testGeoSpatialSearchWithLocationOutsideTheSearchBox(self):
        self.portal.invokeFactory("Location", id="location1", title="Loc 1")
        self.portal.location1.geolocation = "50.2,-7.1"
        self.portal.location1.reindexObject()
        self.maintenance.reindex()
        results = solrSearchResults(
            fq="{!geofilt}", sfield="geolocation", pt="80,123", d=0.2
        )
        self.assertEqual(sorted([r.path_string for r in results]), [])

    # sort='geodist() desc' allows us to sort geolocations by distance.
    # it seems that right now collective.solr filters that param entirely.
    @unittest.skip("Sorting is not working yet.")
    def testGeoSpatialSearchSortByDistance(self):
        self.portal.invokeFactory("Location", id="location1", title="Loc 1")
        self.portal.location1.geolocation = "50,1"
        self.portal.location1.reindexObject()
        self.portal.invokeFactory("Location", id="location2", title="Loc 2")
        self.portal.location2.geolocation = "60,1"
        self.portal.location2.reindexObject()
        self.maintenance.reindex()

        # Query: 52,1 | 50,1 (locaction1) < 60,1 (location2)
        results = solrSearchResults(
            fq="{!bbox}", sfield="geolocation", pt="52,1", d=100, sort="geodist() desc"
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ["/plone/location2", "/plone/location1"],
        )

        # Query: 58,1 | 60,1 (locaction2) < 50,1 (location1)
        results = solrSearchResults(
            fq="{!bbox}", sfield="geolocation", pt="58,1", d=100, sort="geodist() asc"
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ["/plone/location1", "/plone/location2"],
        )


# def test_suite():
#     if pingSolr():
#         return defaultTestLoader.loadTestsFromName(__name__)
#     else:
#         return TestSuite()
