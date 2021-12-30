from collective.solr.testing import activateAndReindex
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from collective.solr.utils import activate
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.restapi.testing import RelativeSession
from plone import api

import unittest
import transaction


class SolrMaintenanceTests(unittest.TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.portal_url = self.portal.absolute_url()

        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.doc = api.content.create(
            container=api.portal.get(),
            type="Document",
            title="Colorless Green Ideas",
        )

        activateAndReindex(self.portal)

        transaction.commit()
        self.api_session = RelativeSession(self.portal_url)
        self.api_session.headers.update({"Accept": "application/json"})
        self.api_session.auth = (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def tearDown(self):
        activate(active=False)

    def test_solr_endpoint_without_q_parameter(self):
        response = self.api_session.get("/@solr")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(6, len(response.json()))

    def test_solr_endpoint(self):
        response = self.api_session.get("/@solr?q=Colorless")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(1, len(response.json()))
        self.assertEqual(response.json()[0]["Title"], "Colorless Green Ideas")

    def test_solr_endpoint_prevent_http_smuggling(self):
        # http smuggling https://github.com/veracode-research/solr-injection#solr-parameters-injection-http-smuggling
        response = self.api_session.get("/@solr?q=Colorless%26xfl=review_state")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Content-Type"), "application/json")
        self.assertEqual(1, len(response.json()))
        self.assertEqual(response.json()[0]["Title"], "Colorless Green Ideas")
