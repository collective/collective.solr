from unittest import TestCase, defaultTestLoader, main
from DateTime import DateTime

from collective.solr.mangler import mangleQuery


def mangle(**keywords):
    mangleQuery(keywords)
    return keywords


class QueryManglerTests(TestCase):

    def testPassUnknownArguments(self):
        keywords = mangle(foo=23, bar=42)
        self.assertEqual(keywords, {'foo': 23, 'bar': 42})

    def testComplainAboutUnknownUsages(self):
        keywords = dict(foo=23, foo_usage='bar:42')
        self.assertRaises(AttributeError, mangleQuery, keywords)

    def testMinRange(self):
        keywords = mangle(foo=(23,), foo_usage='range:min')
        self.assertEqual(keywords, {'foo': '"[23 TO *]"'})

    def testMaxRange(self):
        keywords = mangle(foo=(23,), foo_usage='range:max')
        self.assertEqual(keywords, {'foo': '"[* TO 23]"'})

    def testMinMaxRange(self):
        keywords = mangle(foo=(23,42), foo_usage='range:min:max')
        self.assertEqual(keywords, {'foo': '"[23 TO 42]"'})

    def testDateConversion(self):
        day = DateTime('1972/05/11 UTC')
        keywords = mangle(foo=(day, day + 7), foo_usage='range:min:max')
        self.assertEqual(keywords, {'foo':
            '"[1972-05-11T00:00:00.000Z TO 1972-05-18T00:00:00.000Z]"'})


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')

