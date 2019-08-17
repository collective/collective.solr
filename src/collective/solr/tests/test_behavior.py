# -*- coding: utf-8 -*-
import pkg_resources
import unittest

from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING
from collective.solr.behaviors import ISolrFields
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from collective.solr.testing import activateAndReindex


try:
    pkg_resources.get_distribution("plone.dexterity")
    from plone.dexterity.fti import DexterityFTI

    HAS_DX = True
except pkg_resources.DistributionNotFound:
    HAS_DX = False


@unittest.skipUnless(HAS_DX, "Dexterity not found! Skipping behavior tests.")
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
