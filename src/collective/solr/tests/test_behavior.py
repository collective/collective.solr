import unittest

from collective.solr.behaviors import ISolrFields
from collective.solr.testing import (
    LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING,
    activateAndReindex,
)
from plone.app.testing import TEST_USER_ID, setRoles
from plone.dexterity.fti import DexterityFTI


class BehaviorsTestCase(unittest.TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        activateAndReindex(self.portal)
        setRoles(self.portal, TEST_USER_ID, ["Manager"])

        fti = DexterityFTI("My Dexterity Container")
        self.portal.portal_types._setObject("My Dexterity Container", fti)
        fti.klass = "plone.dexterity.content.Container"
        fti.schema = "zope.interface.Interface"
        fti.behaviors = ("collective.solr.behaviors.ISolrFields",)
        self.portal.invokeFactory("My Dexterity Container", "child")
        self.child = self.portal["child"]

    def test_behavior_showinsearch(self):
        self.assertTrue(ISolrFields(self.child).showinsearch)

    def test_behavior_searchwords(self):
        self.assertEqual(ISolrFields(self.child).searchwords, [])


# EOF
