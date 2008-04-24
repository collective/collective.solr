# -*- coding: utf-8 -*-

from unittest import TestCase, TestSuite, makeSuite, main

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

    def testQuoted(self):
        self.assertEqual(quote('"'), '')
        self.assertEqual(quote('""'), '')
        self.assertEqual(quote('"foo"'), 'foo')
        self.assertEqual(quote('"foo*"'), 'foo*')
        self.assertEqual(quote('"+foo"'), '+foo')
        self.assertEqual(quote('"foo bar"'), 'foo bar')
        self.assertEqual(quote('"foo bar?"'), 'foo bar?')
        self.assertEqual(quote('"-foo +bar"'), '-foo +bar')

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
        self.assertEqual(bq('foo bar'), '+"foo bar"')
        self.assertEqual(bq('john@foo.com'), '+"john@foo.com"')
        self.assertEqual(bq(name='foo'), '+name:foo')
        self.assertEqual(bq(name='foo*'), '+name:"foo\\*"')
        self.assertEqual(bq(name='foo bar'), '+name:"foo bar"')
        self.assertEqual(bq(name='john@foo.com'), '+name:"john@foo.com"')

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

    def testComplexQueries(self):
        bq = self.search.buildQuery
        self.assertEqual(bq('foo', name='"herb*"', cat=(u'bär', '"-hmm"')),
            '+foo +name:herb* +cat:("b\xc3\xa4r" -hmm)')


def test_suite():
    return TestSuite((
        makeSuite(QuoteTests),
        makeSuite(QueryTests),
    ))

if __name__ == '__main__':
    main(defaultTest='test_suite')

