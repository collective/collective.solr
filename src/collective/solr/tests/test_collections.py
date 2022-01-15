import unittest

from collective.solr.contentlisting import FlareContentListingObject
from collective.solr.testing import (
    LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING,
    activateAndReindex,
)
from plone.app.testing import TEST_USER_ID, setRoles


class CollectionsTestCase(unittest.TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        portal = self.portal = self.layer["portal"]
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        id_ = portal.invokeFactory("Collection", id="foo", title="Foo")
        collection = self.collection = portal[id_]
        self.query = query = [
            {
                "i": "SearchableText",
                "o": "plone.app.querystring.operation.string.contains",
                "v": "new",
            }
        ]
        collection.query = query
        activateAndReindex(portal)

    def test_has_results(self):
        # Make sure we get some results
        # If not, then the other tests won't do anything.
        results = self.collection.results()
        self.assertGreater(results.length, 0)
        self.assertTrue(isinstance(results[0], FlareContentListingObject))

    def test_render_collection(self):
        # If it renders, it's good.
        self.collection()

    def test_render_querybuilder_html_results(self):
        # If it renders, it's good.
        collection = self.collection
        view = collection.unrestrictedTraverse("@@querybuilder_html_results")
        view.html_results(self.query)
