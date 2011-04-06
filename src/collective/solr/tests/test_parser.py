from unittest import TestCase
from DateTime import DateTime

from collective.solr.parser import SolrResponse
from collective.solr.parser import SolrSchema
from collective.solr.parser import parseDate
from collective.solr.tests.utils import getData


class ParserTests(TestCase):

    def testParseSimpleSearchResults(self):
        search_response = getData('search_response.txt')
        response = SolrResponse(search_response.split('\n\n', 1)[1])
        results = response.response     # the result set is named 'response'
        self.assertEqual(results.numFound, '1')
        self.assertEqual(results.start, '0')
        match = results[0]
        self.assertEqual(len(results), 1)
        self.assertEqual(match.id, '500')
        self.assertEqual(match.name, 'python test doc')
        self.assertEqual(match.popularity, 0)
        self.assertEqual(match.sku, '500')
        self.assertEqual(match.timestamp,
            DateTime('2008-02-29 16:11:46.998 GMT'))
        headers = response.responseHeader
        self.assertEqual(headers['status'], 0)
        self.assertEqual(headers['QTime'], 0)
        self.assertEqual(headers['params']['wt'], 'xml')
        self.assertEqual(headers['params']['indent'], 'on')
        self.assertEqual(headers['params']['rows'], '10')
        self.assertEqual(headers['params']['q'], 'id:[* TO *]')

    def testParseComplexSearchResults(self):
        complex_xml_response = getData('complex_xml_response.txt')
        response = SolrResponse(complex_xml_response)
        results = response.response     # the result set is named 'response'
        self.assertEqual(results.numFound, '2')
        self.assertEqual(results.start, '0')
        self.assertEqual(len(results), 2)
        first = results[0]
        self.assertEqual(first.cat, ['software', 'search'])
        self.assertEqual(len(first.features), 7)
        self.assertEqual([type(x).__name__ for x in first.features],
            ['str'] * 6 + ['unicode'])
        self.assertEqual(first.id, 'SOLR1000')
        self.assertEqual(first.inStock, True)
        self.assertEqual(first.incubationdate_dt, DateTime('2006/01/17 GMT'))
        self.assertEqual(first.manu, 'Apache Software Foundation')
        self.assertEqual(first.popularity, 10)
        self.assertEqual(first.price, 0.0)
        headers = response.responseHeader
        self.assertEqual(headers['status'], 0)
        self.assertEqual(headers['QTime'], 0)
        self.assertEqual(headers['params']['indent'], 'on')
        self.assertEqual(headers['params']['rows'], '10')
        self.assertEqual(headers['params']['start'], '0')
        self.assertEqual(headers['params']['q'], 'id:[* TO *]')
        self.assertEqual(headers['params']['version'], '2.2')

    def testParseFacetSearchResults(self):
        facet_xml_response = getData('facet_xml_response.txt')
        response = SolrResponse(facet_xml_response)
        results = response.response     # the result set is named 'response'
        self.assertEqual(results.numFound, '1')
        self.assertEqual(results.start, '0')
        self.assertEqual(len(results), 0)
        headers = response.responseHeader
        self.assertEqual(type(headers), type({}))
        self.assertEqual(headers['status'], 0)
        self.assertEqual(headers['QTime'], 1)
        self.assertEqual(headers['params']['facet.limit'], '-1')
        self.assertEqual(headers['params']['rows'], '0')
        self.assertEqual(headers['params']['facet'], 'true')
        self.assertEqual(headers['params']['facet.field'], ['cat', 'inStock'])
        self.assertEqual(headers['params']['indent'], '10')
        self.assertEqual(headers['params']['q'], 'solr')
        counts = response.facet_counts
        self.assertEqual(type(counts), type({}))
        self.assertEqual(counts['facet_queries'], {})
        self.assertEqual(counts['facet_fields']['cat']['electronics'], 0)
        self.assertEqual(counts['facet_fields']['cat']['monitor'], 0)
        self.assertEqual(counts['facet_fields']['cat']['search'], 1)
        self.assertEqual(counts['facet_fields']['cat']['software'], 1)
        self.assertEqual(counts['facet_fields']['inStock']['true'], 1)

    def testParseDateFacetSearchResults(self):
        facet_xml_response = getData('date_facet_xml_response.txt')
        response = SolrResponse(facet_xml_response)
        results = response.response     # the result set is named 'response'
        self.assertEqual(results.numFound, '42')
        self.assertEqual(results.start, '0')
        self.assertEqual(len(results), 0)
        headers = response.responseHeader
        self.assertEqual(type(headers), type({}))
        self.assertEqual(headers['status'], 0)
        self.assertEqual(headers['QTime'], 5)
        self.assertEqual(headers['params']['facet.date'], 'timestamp')
        self.assertEqual(headers['params']['facet.date.start'],
            'NOW/DAY-5DAYS')
        self.assertEqual(headers['params']['facet.date.end'], 'NOW/DAY+1DAY')
        self.assertEqual(headers['params']['facet.date.gap'], '+1DAY')
        self.assertEqual(headers['params']['rows'], '0')
        self.assertEqual(headers['params']['facet'], 'true')
        self.assertEqual(headers['params']['indent'], 'true')
        self.assertEqual(headers['params']['q'], '*:*')
        counts = response.facet_counts
        self.assertEqual(type(counts), type({}))
        self.assertEqual(counts['facet_queries'], {})
        self.assertEqual(counts['facet_fields'], {})
        timestamps = counts['facet_dates']['timestamp']
        self.assertEqual(timestamps['2007-08-11T00:00:00.000Z'], 1)
        self.assertEqual(timestamps['2007-08-12T00:00:00.000Z'], 5)
        self.assertEqual(timestamps['2007-08-13T00:00:00.000Z'], 3)
        self.assertEqual(timestamps['2007-08-14T00:00:00.000Z'], 7)
        self.assertEqual(timestamps['2007-08-15T00:00:00.000Z'], 2)
        self.assertEqual(timestamps['2007-08-16T00:00:00.000Z'], 16)
        self.assertEqual(timestamps['gap'], '+1DAY')
        self.assertEqual(timestamps['end'], DateTime('2007-08-17 GMT'))

    def testParseConfig(self):
        schema_xml = getData('schema.xml')
        schema = SolrSchema(schema_xml.split('\n\n', 1)[1])
        self.assertEqual(len(schema), 21) # 21 items defined in schema.xml
        self.assertEqual(schema['defaultSearchField'], 'text')
        self.assertEqual(schema['uniqueKey'], 'id')
        self.assertEqual(schema['solrQueryParser'].defaultOperator, 'OR')
        self.assertEqual(schema['requiredFields'], ['id', 'name'])
        self.assertEqual(schema['id'].type, 'string')
        self.assertEqual(schema['id'].class_, 'solr.StrField')
        self.assertEqual(schema['id'].required, True)
        self.assertEqual(schema['id'].omitNorms, True)
        self.assertEqual(schema['id'].multiValued, False)
        self.assertEqual(schema['cat'].class_, 'solr.TextField')
        self.assertEqual(schema['cat'].required, False)
        self.assertEqual(schema['cat'].multiValued, True)
        self.assertEqual(schema['cat'].termVectors, True)
        self.assertEqual(schema['sku'].positionIncrementGap, '100')
        self.assertEqual(schema.features.multiValued, True)
        self.assertEqual(schema.weight.class_, 'solr.SortableFloatField')
        self.assertEqual(schema.popularity.class_, 'solr.SortableIntField')
        self.assertEqual(schema.inStock.class_, 'solr.BoolField')
        self.assertEqual(schema.timestamp.class_, 'solr.DateField')
        self.assertEqual(schema.timestamp.default, 'NOW')
        self.assertEqual(schema.timestamp.multiValued, False)
        self.assertEqual(schema.timestamp.indexed, True)
        self.assertEqual(schema.word.indexed, False)
        fields = schema.values()
        self.assertEqual(len([f for f in fields if
            getattr(f, 'required', False)]), 2)
        self.assertEqual(len([f for f in fields if
            getattr(f, 'multiValued', False)]), 3)

    def testParseQuirkyResponse(self):
        quirky_response = getData('quirky_response.txt')
        response = SolrResponse(quirky_response)
        results = response.response     # the result set is named 'response'
        empty_uid = [r for r in results if r.UID == '']
        self.assertEqual(empty_uid, [])


class ParseDateHelperTests(TestCase):

    def testParseDateHelper(self):
        self.assertEqual(parseDate('2007-08-11T00:00:00.000Z'),
            DateTime(2007, 8, 11, 0, 0, 0, 'GMT'))
        self.assertEqual(parseDate('1900-01-01T00:00:00.000Z'),
            DateTime(1900, 1, 1, 0, 0, 0, 'GMT'))
        self.assertEqual(parseDate('999-12-31T00:00:00.000Z'),
            DateTime(999, 12, 31, 0, 0, 0, 'GMT'))
        self.assertEqual(parseDate('99-12-31T00:00:00.000Z'),
            DateTime('0099-12-31T00:00:00.000Z'))
