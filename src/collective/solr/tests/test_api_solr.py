from collective.solr.testing import activateAndReindex
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from collective.solr.utils import activate
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.restapi.testing import RelativeSession

import unittest
import transaction


class SolrMaintenanceTests(unittest.TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()
        activateAndReindex(self.portal)

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
        self.assertEqual(5, len(response.json()))
