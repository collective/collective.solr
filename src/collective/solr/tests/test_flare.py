from unittest import TestCase

from collective.solr.parser import SolrFlare
from collective.solr.flare import PloneFlare


class FlareTests(TestCase):
    def testRelevanceFormatting(self):
        def score(**kw):
            return PloneFlare(SolrFlare(**kw)).data_record_normalized_score_

        self.assertEqual(score(), "n.a.")
        self.assertEqual(score(score=0.04567), "4.6")
        self.assertEqual(score(score="0.04567"), "4.6")
        self.assertEqual(score(score="0.1"), "10.0")
