from unittest import TestCase
from collective.solr.extender import DexteritySearchExtender
from collective.solr.testing import COLLECTIVE_SOLR_INTEGRATION_TESTING


class SearchExtenderBehaviorTest(TestCase):

    layer = COLLECTIVE_SOLR_INTEGRATION_TESTING

    def test_extender_attributes(self):
        class Dummy(object):
            pass
        item = Dummy()
        extended_item = DexteritySearchExtender(item)
        self.assertTrue(hasattr(extended_item, 'showinsearch'))
        self.assertTrue(hasattr(extended_item, 'searchwords'))
