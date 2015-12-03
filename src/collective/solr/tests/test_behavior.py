from unittest import TestCase
from unittest import skip
from collective.solr.extender import DexteritySearchExtender
from collective.solr.testing import COLLECTIVE_SOLR_DEXTERITY_INTEGRATION_TESTING  # noqa E501
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from plone.dexterity.fti import DexterityFTI


class SearchExtenderBehaviorTest(TestCase):

    layer = COLLECTIVE_SOLR_DEXTERITY_INTEGRATION_TESTING

    def test_extender_attributes(self):
        class Dummy(object):
            pass
        item = Dummy()
        extended_item = DexteritySearchExtender(item)
        self.assertTrue(hasattr(extended_item, 'showinsearch'))
        self.assertTrue(hasattr(extended_item, 'searchwords'))

    @skip("AttributeError: showinsearch")
    def test_use_behavior(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Contributor'])
        fti = DexterityFTI('searched_type')
        fti.klass = 'plone.dexterity.content.Item'
        fti.behaviors = ('collective.solr.extender.IElevationFields')
        portal.portal_types._setObject('searched_type', fti)

        test_obj_id = portal.invokeFactory('searched_type', id='test_obj')
        test_obj = portal.get(test_obj_id)
        self.assertEqual(test_obj.showinsearch, True)
        self.assertTrue(hasattr(test_obj, 'searchwords'))
