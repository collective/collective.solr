from unittest import TestCase
from zope.component import provideUtility, getGlobalSiteManager
from DateTime import DateTime

from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.manager import SolrConnectionConfig
from collective.solr.mangler import mangleQuery
from collective.solr.mangler import extractQueryParameters
from collective.solr.mangler import cleanupQueryParameters
from collective.solr.mangler import optimizeQueryParameters
from collective.solr.parser import SolrSchema, SolrField


def mangle(**keywords):
    mangleQuery(keywords, None, {})
    return keywords


class Query:

    def __init__(self, query, range=None, operator=None, depth=None):
        self.query = query
        self.range = range
        self.operator = operator
        self.depth = depth


class QueryManglerTests(TestCase):

    def setUp(self):
        self.config = SolrConnectionConfig()
        provideUtility(self.config, ISolrConnectionConfig)

    def tearDown(self):
        gsm = getGlobalSiteManager()
        gsm.unregisterUtility(self.config, ISolrConnectionConfig)

    def testPassUnknownArguments(self):
        keywords = mangle(foo=23, bar=42)
        self.assertEqual(keywords, {'foo': 23, 'bar': 42})
        keywords = mangle(foo=Query(23), bar=Query(42))
        self.assertEqual(keywords, {'foo': 23, 'bar': 42})

    def testComplainAboutUnknownUsages(self):
        keywords = dict(foo=23, foo_usage='bar:42')
        self.assertRaises(AssertionError, mangleQuery, keywords, None, {})

    def testMinRange(self):
        keywords = mangle(foo=[23], foo_usage='range:min')
        self.assertEqual(keywords, {'foo': '[23 TO *]'})
        keywords = mangle(foo=dict(query=[23], range='min'))
        self.assertEqual(keywords, {'foo': '[23 TO *]'})
        keywords = mangle(foo=Query(query=[23], range='min'))
        self.assertEqual(keywords, {'foo': '[23 TO *]'})

    def testMaxRange(self):
        keywords = mangle(foo=[23], foo_usage='range:max')
        self.assertEqual(keywords, {'foo': '[* TO 23]'})
        keywords = mangle(foo=dict(query=[23], range='max'))
        self.assertEqual(keywords, {'foo': '[* TO 23]'})
        keywords = mangle(foo=dict(query=23, range='max'))
        self.assertEqual(keywords, {'foo': '[* TO 23]'})
        keywords = mangle(foo=Query(query=23, range='max'))
        self.assertEqual(keywords, {'foo': '[* TO 23]'})

    def testMinMaxRange(self):
        keywords = mangle(foo=(23, 42), foo_usage='range:min:max')
        self.assertEqual(keywords, {'foo': '[23 TO 42]'})
        keywords = mangle(foo=dict(query=(23, 42), range='min:max'))
        self.assertEqual(keywords, {'foo': '[23 TO 42]'})
        keywords = mangle(foo=Query(query=(23, 42), range='min:max'))
        self.assertEqual(keywords, {'foo': '[23 TO 42]'})

    def testDateConversion(self):
        day = DateTime('1972/05/11 UTC')
        keywords = mangle(foo=day)
        self.assertEqual(keywords, {'foo': '1972-05-11T00:00:00.000Z'})
        keywords = mangle(foo=(day, day + 7), foo_usage='range:min:max')
        self.assertEqual(keywords, {'foo':
            '[1972-05-11T00:00:00.000Z TO 1972-05-18T00:00:00.000Z]'})
        keywords = mangle(foo=[day], foo_usage='range:min')
        self.assertEqual(keywords, {'foo':
            '[1972-05-11T00:00:00.000Z TO *]'})
        keywords = mangle(foo=dict(query=[day], range='min'))
        self.assertEqual(keywords, {'foo':
            '[1972-05-11T00:00:00.000Z TO *]'})
        keywords = mangle(foo=Query(day))
        self.assertEqual(keywords, {'foo': '1972-05-11T00:00:00.000Z'})

    def testOperatorConversion(self):
        keywords = mangle(foo=(23, 42), foo_usage='operator:or')
        self.assertEqual(keywords, {'foo': '(23 OR 42)'})
        keywords = mangle(foo=dict(query=(23, 42), operator='or'))
        self.assertEqual(keywords, {'foo': '(23 OR 42)'})
        keywords = mangle(foo=Query(query=(23, 42), operator='or'))
        self.assertEqual(keywords, {'foo': '(23 OR 42)'})
        keywords = mangle(foo=(23, 42), foo_usage='operator:and')
        self.assertEqual(keywords, {'foo': '(23 AND 42)'})
        keywords = mangle(foo=dict(query=(23, 42), operator='and'))
        self.assertEqual(keywords, {'foo': '(23 AND 42)'})
        keywords = mangle(foo=Query(query=(23, 42), operator='and'))
        self.assertEqual(keywords, {'foo': '(23 AND 42)'})
        day = DateTime('1972/05/11 UTC')
        keywords = mangle(foo=dict(query=(day, day + 7), operator='or'))
        self.assertEqual(keywords, {'foo':
            '(1972-05-11T00:00:00.000Z OR 1972-05-18T00:00:00.000Z)'})
        keywords = mangle(foo=Query(query=(day, day + 7), operator='or'))
        self.assertEqual(keywords, {'foo':
            '(1972-05-11T00:00:00.000Z OR 1972-05-18T00:00:00.000Z)'})

    def testEffectiveRangeConversion(self):
        day = DateTime('1972/05/11 UTC')
        keywords = mangle(effectiveRange=day, show_inactive=False)
        self.assertEqual(keywords, {
            'effective': '[* TO 1972-05-11T00:00:00.000Z]',
            'expires': '[1972-05-11T00:00:00.000Z TO *]',
        })

    def testEffectiveRangeSteps(self):
        date = DateTime('1972/05/11 03:47:02 UTC')
        # first test with the default step of 1 seconds, i.e. unaltered
        keywords = mangle(effectiveRange=date, show_inactive=False)
        self.assertEqual(keywords, {
            'effective': '[* TO 1972-05-11T03:47:02.000Z]',
            'expires': '[1972-05-11T03:47:02.000Z TO *]',
        })
        # and finally with a setting for steps
        self.config.effective_steps = 300
        keywords = dict(effectiveRange=date, show_inactive=False)
        mangleQuery(keywords, self.config, {})
        self.assertEqual(keywords, {
            'effective': '[* TO 1972-05-11T03:45:00.000Z]',
            'expires': '[1972-05-11T03:45:00.000Z TO *]',
        })

    def testIgnoredParameters(self):
        keywords = mangle(use_solr=True, foo='bar')
        self.assertEqual(keywords, {'foo': 'bar'})
        keywords = mangle(**{'-C': True, 'foo': 'bar'})
        self.assertEqual(keywords, {'foo': 'bar'})


class PathManglerTests(TestCase):

    def testSimplePathQuery(self):
        keywords = mangle(path='/foo')
        self.assertEqual(keywords, {'path_parents': '/foo'})

    def testSimplePathQueryAsDictionary(self):
        keywords = mangle(path=dict(query='/foo'))
        self.assertEqual(keywords, {'path_parents': '/foo'})

    def testSimplePathQueryAsObject(self):
        keywords = mangle(path=Query(query='/foo'))
        self.assertEqual(keywords, {'path_parents': '/foo'})

    def testPathQueryWithDepth(self):
        keywords = mangle(path=dict(query='/foo', depth=-1))
        self.assertEqual(keywords, {'path_parents': '/foo'})
        keywords = mangle(path=dict(query='/foo', depth=0))
        self.assertEqual(keywords, {'path_parents': set([
            '(+path_depth:[2 TO 2] AND +path_parents:/foo)'])})
        keywords = mangle(path=Query(query='/foo', depth=0))
        self.assertEqual(keywords, {'path_parents': set([
            '(+path_depth:[2 TO 2] AND +path_parents:/foo)'])})
        keywords = mangle(path=dict(query='/foo', depth=2))
        self.assertEqual(keywords, {'path_parents': set([
            '(+path_depth:[2 TO 4] AND +path_parents:/foo)'])})
        keywords = mangle(path=Query(query='/foo', depth=2))
        self.assertEqual(keywords, {'path_parents': set([
            '(+path_depth:[2 TO 4] AND +path_parents:/foo)'])})

    def testMultiplePathQuery(self):
        keywords = mangle(path=['/foo', '/bar'])
        self.assertEqual(keywords, {'path_parents': ['/foo', '/bar']})
        keywords = mangle(path=dict(query=['/foo', '/bar']))
        self.assertEqual(keywords, {'path_parents': ['/foo', '/bar']})
        keywords = mangle(path=dict(query=['/foo', '/bar'], depth=-1))
        self.assertEqual(keywords, {'path_parents': ['/foo', '/bar']})
        keywords = mangle(path=dict(query=['/foo', '/bar'], depth=0))
        self.assertEqual(keywords, {'path_parents': set([
            '(+path_depth:[2 TO 2] AND +path_parents:/foo)',
            '(+path_depth:[2 TO 2] AND +path_parents:/bar)'])})
        keywords = mangle(path=dict(query=['/foo', '/bar'], depth=1))
        self.assertEqual(keywords, {'path_parents': set([
            '(+path_depth:[2 TO 3] AND +path_parents:/foo)',
            '(+path_depth:[2 TO 3] AND +path_parents:/bar)'])})
        keywords = mangle(path=dict(query=['/a/b', '/c'], depth=-1))
        self.assertEqual(keywords, {'path_parents': ['/a/b', '/c']})
        keywords = mangle(path=dict(query=['/a/b', '/c'], depth=0))
        self.assertEqual(keywords, {'path_parents': set([
            '(+path_depth:[3 TO 3] AND +path_parents:/a/b)',
            '(+path_depth:[2 TO 2] AND +path_parents:/c)'])})
        keywords = mangle(path=dict(query=['/a/b', '/c'], depth=2))
        self.assertEqual(keywords, {'path_parents': set([
            '(+path_depth:[3 TO 5] AND +path_parents:/a/b)',
            '(+path_depth:[2 TO 4] AND +path_parents:/c)'])})


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

    def testBatchParameters(self):
        extract = extractQueryParameters
        params = extract({'b_start': 5})
        self.assertEqual(params, dict(start=5))
        params = extract({'b_start': '10'})
        self.assertEqual(params, dict(start=10))
        params = extract({'b_size': 5})
        self.assertEqual(params, dict(rows=5))
        params = extract({'b_size': '10'})
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
        params = extract({'facet.field': ('foo', 'bar')})
        self.assertEqual(params, {'facet.field': ('foo', 'bar')})
        # not 'facet*' though
        params = extract({'facetfoo': 'bar'})
        self.assertEqual(params, {})
        # an underscore can be used instead of the '.' for conveniently
        # passing parameters as keyword arguments...
        params = extract(dict(facet_foo='bar'))
        self.assertEqual(params, {'facet.foo': 'bar'})
        params = extract(dict(facet_foo=('foo', 'bar')))
        self.assertEqual(params, {'facet.foo': ('foo', 'bar')})

    def testAllowFilterQueryParameters(self):
        extract = extractQueryParameters
        # 'fq' should be passed on...
        params = extract({'fq': 'foo'})
        self.assertEqual(params, {'fq': 'foo'})
        params = extract({'fq': ['foo', 'bar']})
        self.assertEqual(params, {'fq': ['foo', 'bar']})

    def testAllowFieldListParameter(self):
        extract = extractQueryParameters
        # 'fl' should be passed on...
        params = extract({'fl': 'foo'})
        self.assertEqual(params, {'fl': 'foo'})
        params = extract({'fl': ['foo', 'bar']})
        self.assertEqual(params, {'fl': ['foo', 'bar']})

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

    def testFilterQuerySubstitution(self):
        def optimize(**params):
            query = dict(a='a:23', b='b:42', c='c:(23 42)')
            optimizeQueryParameters(query, params)
            return query, params
        # first test without the configuration utility
        self.assertEqual(optimize(),
            (dict(a='a:23', b='b:42', c='c:(23 42)'), dict()))
        # now unconfigured...
        config = SolrConnectionConfig()
        provideUtility(config, ISolrConnectionConfig)
        self.assertEqual(optimize(),
            (dict(a='a:23', b='b:42', c='c:(23 42)'), dict()))
        config.filter_queries = ['a']
        self.assertEqual(optimize(),
            (dict(b='b:42', c='c:(23 42)'), dict(fq=['a:23'])))
        self.assertEqual(optimize(fq='x:13'),
            (dict(b='b:42', c='c:(23 42)'), dict(fq=['x:13', 'a:23'])))
        self.assertEqual(optimize(fq=['x:13', 'y:17']),
            (dict(b='b:42', c='c:(23 42)'), dict(fq=['x:13', 'y:17', 'a:23'])))
        config.filter_queries = ['a', 'c']
        self.assertEqual(optimize(),
            (dict(b='b:42'), dict(fq=['a:23', 'c:(23 42)'])))
        self.assertEqual(optimize(fq='x:13'),
            (dict(b='b:42'), dict(fq=['x:13', 'a:23', 'c:(23 42)'])))
        self.assertEqual(optimize(fq=['x:13', 'y:17']),
            (dict(b='b:42'), dict(fq=['x:13', 'y:17', 'a:23', 'c:(23 42)'])))
        # also test substitution of combined filter queries
        config.filter_queries = ['a c']
        self.assertEqual(optimize(),
            (dict(b='b:42'), dict(fq=['a:23 c:(23 42)'])))
        config.filter_queries = ['a c', 'b']
        self.assertEqual(optimize(),
            ({'*': '*:*'}, dict(fq=['a:23 c:(23 42)', 'b:42'])))
        # for multiple matches the first takes precedence
        config.filter_queries = ['a', 'a c', 'b']
        self.assertEqual(optimize(),
            (dict(c='c:(23 42)'), dict(fq=['a:23', 'b:42'])))
        # parameters not contained in the query must not be converted
        config.filter_queries = ['a nonexisting', 'b']
        self.assertEqual(optimize(),
            (dict(a='a:23', c='c:(23 42)'), dict(fq=['b:42'])))

    def testFilterFacetDependencies(self):
        extract = extractQueryParameters
        # any info about facet dependencies must not be passed on to solr
        params = extract({'facet.field': 'foo:bar', 'facet.foo': 'bar:foo'})
        self.assertEqual(params, {'facet.field': 'foo', 'facet.foo': 'bar'})
        params = extract({'facet.field': ('foo:bar', 'bar:foo')})
        self.assertEqual(params, {'facet.field': ('foo', 'bar')})
        # also check the "underscore" variant...
        params = extract(dict(facet_foo='bar:foo'))
        self.assertEqual(params, {'facet.foo': 'bar'})
        params = extract(dict(facet_foo=('foo:bar', 'bar:foo')))
        self.assertEqual(params, {'facet.foo': ('foo', 'bar')})
