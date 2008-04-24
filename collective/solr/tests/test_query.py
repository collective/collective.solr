# -*- coding: utf-8 -*-

from unittest import TestCase, TestSuite, makeSuite, main

from collective.solr.search import quote


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


def test_suite():
    return TestSuite((
        makeSuite(QuoteTests),
    ))

if __name__ == '__main__':
    main(defaultTest='test_suite')

