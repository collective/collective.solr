from unittest import TestCase, defaultTestLoader, main
from DateTime import DateTime

from collective.solr.mangler import mangleQuery
from collective.solr.mangler import extractQueryParameters
from collective.solr.mangler import cleanupQueryParameters
from collective.solr.parser import SolrSchema, SolrField


def mangle(**keywords):
    mangleQuery(keywords)
    return keywords


class Query:

    def __init__(self, query, range=None, operator=None, depth=None):
        self.query = query
        self.range = range
        self.operator = operator
        self.depth = depth


class QueryManglerTests(TestCase):

    def testPassUnknownArguments(self):
        keywords = mangle(foo=23, bar=42)
        self.assertEqual(keywords, {'foo': 23, 'bar': 42})
        keywords = mangle(foo=Query(23), bar=Query(42))
        self.assertEqual(keywords, {'foo': 23, 'bar': 42})

    def testComplainAboutUnknownUsages(self):
        keywords = dict(foo=23, foo_usage='bar:42')
        self.assertRaises(AssertionError, mangleQuery, keywords)

    def testMinRange(self):
        keywords = mangle(foo=[23], foo_usage='range:min')
        self.assertEqual(keywords, {'foo': '"[23 TO *]"'})
        keywords = mangle(foo=dict(query=[23], range='min'))
        self.assertEqual(keywords, {'foo': '"[23 TO *]"'})
        keywords = mangle(foo=Query(query=[23], range='min'))
        self.assertEqual(keywords, {'foo': '"[23 TO *]"'})

    def testMaxRange(self):
        keywords = mangle(foo=[23], foo_usage='range:max')
        self.assertEqual(keywords, {'foo': '"[* TO 23]"'})
        keywords = mangle(foo=dict(query=[23], range='max'))
        self.assertEqual(keywords, {'foo': '"[* TO 23]"'})
        keywords = mangle(foo=dict(query=23, range='max'))
        self.assertEqual(keywords, {'foo': '"[* TO 23]"'})
        keywords = mangle(foo=Query(query=23, range='max'))
        self.assertEqual(keywords, {'foo': '"[* TO 23]"'})

    def testMinMaxRange(self):
        keywords = mangle(foo=(23, 42), foo_usage='range:min:max')
        self.assertEqual(keywords, {'foo': '"[23 TO 42]"'})
        keywords = mangle(foo=dict(query=(23, 42), range='min:max'))
        self.assertEqual(keywords, {'foo': '"[23 TO 42]"'})
        keywords = mangle(foo=Query(query=(23, 42), range='min:max'))
        self.assertEqual(keywords, {'foo': '"[23 TO 42]"'})

    def testDateConversion(self):
        day = DateTime('1972/05/11 UTC')
        keywords = mangle(foo=day)
        self.assertEqual(keywords, {'foo': '1972-05-11T00:00:00.000Z'})
        keywords = mangle(foo=(day, day + 7), foo_usage='range:min:max')
        self.assertEqual(keywords, {'foo':
            '"[1972-05-11T00:00:00.000Z TO 1972-05-18T00:00:00.000Z]"'})
        keywords = mangle(foo=[day], foo_usage='range:min')
        self.assertEqual(keywords, {'foo':
            '"[1972-05-11T00:00:00.000Z TO *]"'})
        keywords = mangle(foo=dict(query=[day], range='min'))
        self.assertEqual(keywords, {'foo':
            '"[1972-05-11T00:00:00.000Z TO *]"'})
        keywords = mangle(foo=Query(day))
        self.assertEqual(keywords, {'foo': '1972-05-11T00:00:00.000Z'})

    def testOperatorConversion(self):
        keywords = mangle(foo=(23, 42), foo_usage='operator:or')
        self.assertEqual(keywords, {'foo': '"(23 OR 42)"'})
        keywords = mangle(foo=dict(query=(23, 42), operator='or'))
        self.assertEqual(keywords, {'foo': '"(23 OR 42)"'})
        keywords = mangle(foo=Query(query=(23, 42), operator='or'))
        self.assertEqual(keywords, {'foo': '"(23 OR 42)"'})
        keywords = mangle(foo=(23, 42), foo_usage='operator:and')
        self.assertEqual(keywords, {'foo': '"(23 AND 42)"'})
        keywords = mangle(foo=dict(query=(23, 42), operator='and'))
        self.assertEqual(keywords, {'foo': '"(23 AND 42)"'})
        keywords = mangle(foo=Query(query=(23, 42), operator='and'))
        self.assertEqual(keywords, {'foo': '"(23 AND 42)"'})
        day = DateTime('1972/05/11 UTC')
        keywords = mangle(foo=dict(query=(day, day + 7), operator='or'))
        self.assertEqual(keywords, {'foo':
            '"(1972-05-11T00:00:00.000Z OR 1972-05-18T00:00:00.000Z)"'})
        keywords = mangle(foo=Query(query=(day, day + 7), operator='or'))
        self.assertEqual(keywords, {'foo':
            '"(1972-05-11T00:00:00.000Z OR 1972-05-18T00:00:00.000Z)"'})

    def testBooleanConversion(self):
        keywords = mangle(foo=False)
        self.assertEqual(keywords, {'foo': 'false'})
        keywords = mangle(foo=True)
        self.assertEqual(keywords, {'foo': 'true'})

    def testEffectiveRangeConversion(self):
        day = DateTime('1972/05/11 UTC')
        keywords = mangle(effectiveRange=day)
        self.assertEqual(keywords, {
            'effective': '"[* TO 1972-05-11T00:00:00.000Z]"',
            'expires': '"[1972-05-11T00:00:00.000Z TO *]"',
        })


class PathManglerTests(TestCase):

    def testSimplePathQuery(self):
        keywords = mangle(path='/foo')
        self.assertEqual(keywords, {'parentPaths': '/foo'})

    def testSimplePathQueryAsDictionary(self):
        keywords = mangle(path=dict(query='/foo'))
        self.assertEqual(keywords, {'parentPaths': '/foo'})

    def testSimplePathQueryAsObject(self):
        keywords = mangle(path=Query(query='/foo'))
        self.assertEqual(keywords, {'parentPaths': '/foo'})

    def testPathQueryWithLevel(self):
        keywords = mangle(path=dict(query='/foo', depth=0))
        self.assertEqual(keywords, {'parentPaths': '/foo',
            'physicalDepth': '"[* TO 2]"'})
        keywords = mangle(path=Query(query='/foo', depth=0))
        self.assertEqual(keywords, {'parentPaths': '/foo',
            'physicalDepth': '"[* TO 2]"'})
        keywords = mangle(path=dict(query='/foo', depth=2))
        self.assertEqual(keywords, {'parentPaths': '/foo',
            'physicalDepth': '"[* TO 4]"'})
        keywords = mangle(path=Query(query='/foo', depth=2))
        self.assertEqual(keywords, {'parentPaths': '/foo',
            'physicalDepth': '"[* TO 4]"'})


class QueryParameterTests(TestCase):

    def testSortIndex(self):
        extract = extractQueryParameters
        params = extract({'sort_on': 'foo'})
        self.assertEqual(params, dict(sort='foo asc'))
        # again with dashed instead of underscores
        params = extract({'sort-on': 'foo'})
        self.assertEqual(params, dict(sort='foo asc'))

    def testSortOrder(self):
        extract = extractQueryParameters
        params = extract({'sort_on': 'foo', 'sort_order': 'ascending'})
        self.assertEqual(params, dict(sort='foo asc'))
        params = extract({'sort_on': 'foo', 'sort_order': 'descending'})
        self.assertEqual(params, dict(sort='foo desc'))
        params = extract({'sort_on': 'foo', 'sort_order': 'reverse'})
        self.assertEqual(params, dict(sort='foo desc'))
        params = extract({'sort_on': 'foo', 'sort_order': 'bar'})
        self.assertEqual(params, dict(sort='foo asc'))
        # again with dashed instead of underscores
        params = extract({'sort-on': 'foo', 'sort-order': 'ascending'})
        self.assertEqual(params, dict(sort='foo asc'))
        params = extract({'sort-on': 'foo', 'sort-order': 'descending'})
        self.assertEqual(params, dict(sort='foo desc'))
        params = extract({'sort-on': 'foo', 'sort-order': 'reverse'})
        self.assertEqual(params, dict(sort='foo desc'))
        params = extract({'sort-on': 'foo', 'sort-order': 'bar'})
        self.assertEqual(params, dict(sort='foo asc'))

    def testSortLimit(self):
        extract = extractQueryParameters
        params = extract({'sort_limit': 5})
        self.assertEqual(params, dict(rows=5))
        params = extract({'sort_limit': '10'})
        self.assertEqual(params, dict(rows=10))
        # again with dashed instead of underscores
        params = extract({'sort-limit': 5})
        self.assertEqual(params, dict(rows=5))
        params = extract({'sort-limit': '10'})
        self.assertEqual(params, dict(rows=10))

    def testCombined(self):
        extract = extractQueryParameters
        params = extract({'sort_on': 'foo', 'sort_limit': 5})
        self.assertEqual(params, dict(sort='foo asc', rows=5))
        params = extract({'sort_on': 'foo', 'sort_order': 'reverse',
                          'sort_limit': 5})
        self.assertEqual(params, dict(sort='foo desc', rows=5))
        params = extract({'sort_order': 'reverse', 'sort_limit': 5})
        self.assertEqual(params, dict(rows=5))

    def testAllowFacetParameters(self):
        extract = extractQueryParameters
        # 'facet' and 'facet.*' should be passed on...
        params = extract({'facet': 'true'})
        self.assertEqual(params, {'facet': 'true'})
        params = extract({'facet.field': 'foo', 'facet.foo': 'bar'})
        self.assertEqual(params, {'facet.field': 'foo', 'facet.foo': 'bar'})
        # not 'facet*' though
        params = extract({'facetfoo': 'bar'})
        self.assertEqual(params, {})
        # an underscore can be used instead of the '.' for conveniently
        # passing parameters as keyword arguments...
        params = extract(dict(facet_foo='bar'))
        self.assertEqual(params, {'facet.foo': 'bar'})

    def testSortIndexCleanup(self):
        cleanup = cleanupQueryParameters
        schema = SolrSchema()
        # a non-existing sort index should be removed
        params = cleanup(dict(sort='foo asc'), schema)
        self.assertEqual(params, dict())
        # the same goes when the given index isn't indexed
        schema['foo'] = SolrField(indexed=False)
        params = cleanup(dict(sort='foo asc'), schema)
        self.assertEqual(params, dict())
        # a suitable index will be left intact, of course...
        schema['foo'].indexed = True
        params = cleanup(dict(sort='foo asc'), schema)
        self.assertEqual(params, dict(sort='foo asc'))
        # also make sure sort index aliases work, if the alias index exists
        params = cleanup(dict(sort='sortable_title asc'), schema)
        self.assertEqual(params, dict())
        schema['Title'] = SolrField(indexed=True)
        params = cleanup(dict(sort='sortable_title asc'), schema)
        self.assertEqual(params, dict(sort='Title asc'))


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')
