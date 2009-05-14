from unittest import TestCase, defaultTestLoader, main

from collective.solr.flare import PloneFlare


class Dummy:
    """" dummy class for testing purposes """

    def __init__(self, **kw):
        self.__dict__.update(kw)


class FlareTests(TestCase):

    def testRelevanceFormatting(self):
        def score(**kw):
            return PloneFlare(Dummy(**kw)).data_record_normalized_score_
        self.assertEqual(score(), 'n.a.')
        self.assertEqual(score(score=0.04567), '4.6')
        self.assertEqual(score(score='0.04567'), '4.6')
        self.assertEqual(score(score='0.1'), '10.0')


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')
