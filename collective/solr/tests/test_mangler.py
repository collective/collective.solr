from unittest import TestCase, defaultTestLoader, main
from DateTime import DateTime

from collective.solr.mangler import mangleQuery


class QueryManglerTests(TestCase):

    def testPassUnknownArguments(self):
        keywords = dict(foo=23, bar=42)
        mangleQuery(keywords)
        self.assertEqual(keywords, {'foo': 23, 'bar': 42})

    def testComplainAboutUnknownUsages(self):
        keywords = dict(foo=23, foo_usage='bar:42')
        self.assertRaises(AttributeError, mangleQuery, keywords)

    def testMinRange(self):
        keywords = dict(foo=(23,), foo_usage='range:min')
        mangleQuery(keywords)
        self.assertEqual(keywords, {'foo': '"[23 TO *]"'})

    def testMaxRange(self):
        keywords = dict(foo=(23,), foo_usage='range:max')
        mangleQuery(keywords)
        self.assertEqual(keywords, {'foo': '"[* TO 23]"'})

    def testMinMaxRange(self):
        keywords = dict(foo=(23,42), foo_usage='range:min:max')
        mangleQuery(keywords)
        self.assertEqual(keywords, {'foo': '"[23 TO 42]"'})

    def testDateConversion(self):
        start = DateTime('1972/05/11 UTC')
        end = start + 7
        keywords = dict(foo=(start, end), foo_usage='range:min:max')
        mangleQuery(keywords)
        self.assertEqual(keywords, {'foo': '"[1972-05-11T00:00:00.000Z TO 1972-05-18T00:00:00.000Z]"'})


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')

