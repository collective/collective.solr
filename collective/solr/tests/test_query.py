# -*- coding: utf-8 -*-

from unittest import TestCase, defaultTestLoader, main
from DateTime import DateTime
from zope.component import provideUtility

from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.manager import SolrConnectionConfig
from collective.solr.manager import SolrConnectionManager
from collective.solr.tests.utils import getData, fakehttp
from collective.solr.search import quote, Search


class QuoteTests(TestCase):

    def testQuoting(self):
        self.assertEqual(quote('foo'), 'foo')
        self.assertEqual(quote('foo '), '"foo "')
        self.assertEqual(quote('"foo'), '"\\"foo"')
        self.assertEqual(quote('foo"'), '"foo\\""')
        self.assertEqual(quote('foo bar'), '"foo bar"')
        self.assertEqual(quote('foo bar what?'), '"foo bar what\?"')
        self.assertEqual(quote('[]'), '"\[\]"')
        self.assertEqual(quote('()'), '"\(\)"')
        self.assertEqual(quote('{}'), '"\{\}"')
        self.assertEqual(quote('...""'), '"...\\"\\""')
        self.assertEqual(quote('\\'), '"\\"')
        self.assertEqual(quote('-+&|!^~*?:'), '"\\-\\+\\&\\|\\!\\^\\~\\*\\?\\:"')
        self.assertEqual(quote('john@foo.com'), '"john@foo.com"')
        self.assertEqual(quote(' '), '" "')
        self.assertEqual(quote(''), '""')

    def testQuoted(self):
        self.assertEqual(quote('"'), '')
        self.assertEqual(quote('""'), '')
        self.assertEqual(quote('"foo"'), 'foo')
        self.assertEqual(quote('"foo*"'), 'foo*')
        self.assertEqual(quote('"+foo"'), '+foo')
        self.assertEqual(quote('"foo bar"'), 'foo bar')
        self.assertEqual(quote('"foo bar?"'), 'foo bar?')
        self.assertEqual(quote('"-foo +bar"'), '-foo +bar')
        self.assertEqual(quote('" "'), '" "')
        self.assertEqual(quote('""'), '')

    def testUnicode(self):
        self.assertEqual(quote('foø'), '"fo\xc3\xb8"')
        self.assertEqual(quote('"foø'), '"\\"fo\xc3\xb8"')
        self.assertEqual(quote('whät?'), '"wh\xc3\xa4t\?"')
        self.assertEqual(quote('[ø]'), '"\[\xc3\xb8\]"')
        self.assertEqual(quote('"foø*"'), 'fo\xc3\xb8*')
        self.assertEqual(quote('"foø bar?"'), 'fo\xc3\xb8 bar?')
        self.assertEqual(quote(u'john@foo.com'), '"john@foo.com"')


class QueryTests(TestCase):

    def setUp(self):
        provideUtility(SolrConnectionConfig(), ISolrConnectionConfig)
        self.mngr = SolrConnectionManager()
        self.mngr.setHost(active=True)
        conn = self.mngr.getConnection()
        fakehttp(conn, getData('schema.xml'))       # fake schema response
        self.mngr.getSchema()                       # read and cache the schema
        self.search = Search()
        self.search.manager = self.mngr

    def tearDown(self):
        self.mngr.closeConnection()
        self.mngr.setHost(active=False)

    def testSimpleQueries(self):
        bq = self.search.buildQuery
        self.assertEqual(bq('foo'), '+foo')
        self.assertEqual(bq('foo*'), '+"foo\\*"')
        self.assertEqual(bq('foo!'), '+"foo\\!"')
        self.assertEqual(bq('(foo)'), '+"\\(foo\\)"')
        self.assertEqual(bq('(foo...'), '+"\\(foo..."')
        self.assertEqual(bq('foo bar'), '+"foo bar"')
        self.assertEqual(bq('john@foo.com'), '+"john@foo.com"')
        self.assertEqual(bq(name='foo'), '+name:foo')
        self.assertEqual(bq(name='foo*'), '+name:"foo\\*"')
        self.assertEqual(bq(name='foo bar'), '+name:"foo bar"')
        self.assertEqual(bq(name='john@foo.com'), '+name:"john@foo.com"')
        self.assertEqual(bq(name=' '), '+name:" "')
        self.assertEqual(bq(name=''), '')

    def testMultiValueQueries(self):
        bq = self.search.buildQuery
        self.assertEqual(bq(('foo', 'bar')), '+(foo bar)')
        self.assertEqual(bq(('foo', 'bar*')), '+(foo "bar\\*")')
        self.assertEqual(bq(('foo bar', 'hmm')), '+("foo bar" hmm)')
        self.assertEqual(bq(name=['foo', 'bar']), '+name:(foo bar)')
        self.assertEqual(bq(name=['foo', 'bar*']), '+name:(foo "bar\\*")')
        self.assertEqual(bq(name=['foo bar', 'hmm']), '+name:("foo bar" hmm)')

    def testMultiArgumentQueries(self):
        bq = self.search.buildQuery
        self.assertEqual(bq('foo', name='bar'), '+foo +name:bar')
        self.assertEqual(bq('foo', name=('bar', 'hmm')), '+foo +name:(bar hmm)')
        self.assertEqual(bq(name='foo', cat='bar'), '+name:foo +cat:bar')
        self.assertEqual(bq(name='foo', cat=['bar', 'hmm']), '+name:foo +cat:(bar hmm)')
        self.assertEqual(bq('foo', name=' '), '+foo +name:" "')
        self.assertEqual(bq('foo', name=''), '+foo')

    def testInvalidArguments(self):
        bq = self.search.buildQuery
        self.assertEqual(bq(title='foo'), '')
        self.assertEqual(bq(title='foo', name='bar'), '+name:bar')
        self.assertEqual(bq('bar', title='foo'), '+bar')

    def testUnicodeArguments(self):
        bq = self.search.buildQuery
        self.assertEqual(bq(u'foo'), '+foo')
        self.assertEqual(bq(u'foø'), '+"fo\xc3\xb8"')
        self.assertEqual(bq(u'john@foo.com'), '+"john@foo.com"')
        self.assertEqual(bq(name=['foo', u'bar']), '+name:(foo bar)')
        self.assertEqual(bq(name=['foo', u'bär']), '+name:(foo "b\xc3\xa4r")')
        self.assertEqual(bq(name='foo', cat=(u'bar', 'hmm')), '+name:foo +cat:(bar hmm)')
        self.assertEqual(bq(name='foo', cat=(u'bär', 'hmm')), '+name:foo +cat:("b\xc3\xa4r" hmm)')
        self.assertEqual(bq(name=u'john@foo.com', cat='spammer'), '+name:"john@foo.com" +cat:spammer')

    def testQuotedQueries(self):
        bq = self.search.buildQuery
        self.assertEqual(bq('"foo"'), 'foo')
        self.assertEqual(bq('"foo*"'), 'foo*')
        self.assertEqual(bq('"+foo"'), '+foo')
        self.assertEqual(bq('"foo bar"'), 'foo bar')
        self.assertEqual(bq('"foo bar?"'), 'foo bar?')
        self.assertEqual(bq('"-foo +bar"'), '-foo +bar')
        self.assertEqual(bq(name='"foo"'), '+name:foo')
        self.assertEqual(bq(name='"foo bar'), '+name:"\\"foo bar"')
        self.assertEqual(bq(name='"foo bar*'), '+name:"\\"foo bar\\*"')
        self.assertEqual(bq(name='"-foo"', timestamp='"[* TO NOW]"'),
            '+timestamp:[* TO NOW] +name:-foo')
        self.assertEqual(bq(name='"john@foo.com"'), '+name:john@foo.com')
        self.assertEqual(bq(name='" "'), '+name:" "')
        self.assertEqual(bq(name='""'), '')

    def testComplexQueries(self):
        bq = self.search.buildQuery
        self.assertEqual(bq('foo', name='"herb*"', cat=(u'bär', '"-hmm"')),
            '+foo +name:herb* +cat:("b\xc3\xa4r" -hmm)')

    def testBooleanQueries(self):
        bq = self.search.buildQuery
        self.assertEqual(bq(inStock=True), '+inStock:true')
        self.assertEqual(bq(inStock=False), '+inStock:false')


class InactiveQueryTests(TestCase):

    def testUnavailableSchema(self):
        provideUtility(SolrConnectionConfig(), ISolrConnectionConfig)
        search = Search()
        search.manager = SolrConnectionManager()
        self.assertEqual(search.buildQuery('foo'), '')
        self.assertEqual(search.buildQuery(name='foo'), '')


class SearchTests(TestCase):

    def setUp(self):
        provideUtility(SolrConnectionConfig(), ISolrConnectionConfig)
        self.mngr = SolrConnectionManager()
        self.mngr.setHost(active=True)
        self.conn = self.mngr.getConnection()
        self.search = Search()
        self.search.manager = self.mngr

    def tearDown(self):
        self.mngr.closeConnection()
        self.mngr.setHost(active=False)

    def testSimpleSearch(self):
        schema = getData('schema.xml')
        search = getData('search_response.txt')
        request = getData('search_request.txt')
        output = fakehttp(self.conn, schema, search)    # fake responses
        query = self.search.buildQuery('"id:[* TO *]"')
        results = self.search(query, rows=10, wt='xml', indent='on').results()
        normalize = lambda x: sorted(x.split('&'))      # sort request params
        self.assertEqual(normalize(output.get(skip=1)), normalize(request))
        self.assertEqual(results.numFound, '1')
        self.assertEqual(len(results), 1)
        match = results[0]
        self.assertEqual(match.id, '500')
        self.assertEqual(match.name, 'python test doc')
        self.assertEqual(match.popularity, 0)
        self.assertEqual(match.sku, '500')
        self.assertEqual(match.timestamp, DateTime('2008-02-29 16:11:46.998 GMT'))


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')

