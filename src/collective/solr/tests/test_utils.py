# -*- coding: utf-8 -*-

from unittest import TestCase
from Testing import ZopeTestCase as ztc

from collective.solr.tests.utils import getData
from collective.solr.parser import SolrResponse
from collective.solr.utils import findObjects, isSimpleTerm, isSimpleSearch
from collective.solr.utils import isWildCard
from collective.solr.utils import setupTranslationMap, prepareData
from collective.solr.utils import padResults


class UtilsTests(ztc.ZopeTestCase):

    def afterSetUp(self):
        self.app.manage_addFolder(id='portal', title='Portal')
        self.portal = self.app.portal
        self.portal.manage_addFolder(id='foo', title='Foo')
        self.portal.foo.manage_addFolder(id='bar', title='Bar')
        self.portal.foo.bar.manage_addDocument(id='doc1', title='a document')
        self.portal.foo.bar.manage_addDocument(id='file1', title='a file')
        self.portal.manage_addFolder(id='bar', title='Bar')
        self.portal.bar.manage_addFolder(id='foo', title='Foo')
        self.portal.bar.foo.manage_addDocument(id='doc2', title='a document')
        self.portal.bar.foo.manage_addDocument(id='file2', title='a file')
        self.good = ('bar', 'bar/foo', 'bar/foo/doc2', 'bar/foo/file2',
            'foo', 'foo/bar', 'foo/bar/doc1', 'foo/bar/file1')

    def ids(self, results):
        return tuple(sorted([r[0] for r in results]))

    def testZopeFindAndApply(self):
        found = self.app.ZopeFindAndApply(self.portal, search_sub=True)
        self.assertEqual(self.ids(found), self.good)

    def testFindObjects(self):
        found = list(findObjects(self.portal))
        # the starting point itself is returned
        self.assertEqual(found[0], ('', self.portal))
        # but the rest should be the same...
        self.assertEqual(self.ids(found[1:]), self.good)

    def testSimpleTerm(self):
        self.failUnless(isSimpleTerm('foo'))
        self.failUnless(isSimpleTerm('foo '))
        self.failUnless(isSimpleTerm(u'føø'))
        self.failUnless(isSimpleTerm('føø'))
        self.failIf(isSimpleTerm('foo!'))
        self.failIf(isSimpleTerm('"foo"'))
        self.failIf(isSimpleTerm(u'føø!'))
        self.failIf(isSimpleTerm(unicode('föö', 'latin')))
        self.failIf(isSimpleTerm('foo42'))
        self.failIf(isSimpleTerm('foo 42'))
        self.failIf(isSimpleTerm('42 foo'))
        self.failUnless(isSimpleTerm('42foo'))

    def testSimpleSearch(self):
        self.failUnless(isSimpleSearch('foo'))
        self.failUnless(isSimpleSearch('foo bar'))
        self.failUnless(isSimpleSearch('foo bar '))
        self.failUnless(isSimpleSearch('foo   bar'))
        self.failUnless(isSimpleSearch(u'føø bär'))
        self.failUnless(isSimpleSearch('føø bär'))
        self.failUnless(isSimpleSearch('foo*'))
        self.failUnless(isSimpleSearch('foo* bar*'))
        self.failUnless(isSimpleSearch('*foo*'))
        self.failUnless(isSimpleSearch('"foo"'))
        self.failUnless(isSimpleSearch('"foo bar"'))
        self.failUnless(isSimpleSearch('"foo AND bar"'))
        self.failUnless(isSimpleSearch('foo "AND" bar'))
        self.failUnless(isSimpleSearch('"foo" "bar"'))
        self.failUnless(isSimpleSearch('fo?bar'))
        self.failUnless(isSimpleSearch('foo bar?'))
        self.failUnless(isSimpleSearch('areallyverylongword '
            'andanotherreallylongwordwithsomecake'))
        self.failUnless(isSimpleSearch('areallyverylongword '
            'andanotherreallylongwordwithsomecake *'))
        self.failIf(isSimpleSearch(''))
        self.failIf(isSimpleSearch(u'føø bär!'))
        self.failIf(isSimpleSearch(unicode('föö bär', 'latin')))
        self.failIf(isSimpleSearch('foo AND bar'))
        self.failIf(isSimpleSearch('foo OR bar'))
        self.failIf(isSimpleSearch('foo NOT bar'))
        self.failIf(isSimpleSearch('"foo" OR bar'))
        self.failIf(isSimpleSearch('(foo OR bar)'))
        self.failIf(isSimpleSearch('+foo'))
        self.failIf(isSimpleSearch('name:foo'))
        self.failIf(isSimpleSearch('foo && bar'))
        self.failIf(isSimpleSearch('2000'))
        self.failIf(isSimpleSearch('foo 2000'))
        self.failIf(isSimpleSearch('foo 1/2000'))
        self.failIf(isSimpleSearch('foo 42 bar11'))
        self.failUnless(isSimpleSearch('2000 foo'))

    def testIsWildCard(self):
        self.failUnless(isWildCard('foo*'))
        self.failUnless(isWildCard('fo?'))
        self.failUnless(isWildCard('fo?o'))
        self.failUnless(isWildCard('fo*oo'))
        self.failUnless(isWildCard('fo?o*'))
        self.failUnless(isWildCard('*foo'))
        self.failUnless(isWildCard('*foo*'))
        self.failUnless(isWildCard('foo* bar'))
        self.failUnless(isWildCard('foo bar?'))
        self.failUnless(isWildCard('*'))
        self.failUnless(isWildCard('?'))
        self.failUnless(isWildCard(u'føø*'))
        self.failUnless(isWildCard(u'føø*'.encode('utf-8')))
        self.failUnless(isWildCard(u'*føø*'))
        self.failIf(isWildCard('foo'))
        self.failIf(isWildCard('fo#o'))
        self.failIf(isWildCard('foo bar'))
        self.failIf(isWildCard(u'føø'))
        self.failIf(isWildCard(u'føø'.encode('utf-8')))
        # other characters might be meaningful in solr, but we don't
        # distinguish them properly (yet)
        self.failIf(isWildCard('foo#?'))


class TranslationTests(TestCase):

    def testTranslationMap(self):
        tm = setupTranslationMap()
        self.assertEqual('\f\a\b'.translate(tm), ' ' * 3)
        self.assertEqual('foo\nbar'.translate(tm), 'foo\nbar')
        self.assertEqual('foo\n\tbar\a\f\r'.translate(tm), 'foo\n\tbar  \r')

    def testRemoveControlCharacters(self):
        data = {'SearchableText': 'foo\n\tbar\a\f\r'}
        prepareData(data)
        self.assertEqual(data, {'SearchableText': 'foo\n\tbar  \r'})

    def testUnicodeSearchableText(self):
        data = {'SearchableText': u'f\xf8\xf8 bar'}
        prepareData(data)
        self.assertEqual(data, {'SearchableText': 'f\xc3\xb8\xc3\xb8 bar'})


class BatchingHelperTests(TestCase):

    def results(self):
        xml_response = getData('quirky_response.txt')
        response = SolrResponse(xml_response)
        return response.response        # the result set is named 'response'

    def testResult(self):
        results = self.results()
        self.assertEqual(results.numFound, '1204')
        self.assertEqual(len(results), 137)
        self.assertEqual(results[0].UID, '7c31adb20d5eee314233abfe48515cf3')

    def testResultsPadding(self):
        results = self.results()
        padResults(results)
        self.assertEqual(len(results), 1204)
        self.assertEqual(results[0].UID, '7c31adb20d5eee314233abfe48515cf3')
        self.assertEqual(results[137:], [None] * (1204 - 137))

    def testResultsPaddingWithStart(self):
        results = self.results()
        padResults(results, start=50)
        self.assertEqual(len(results), 1204)
        self.assertEqual(results[:50], [None] * 50)
        self.assertEqual(results[50].UID, '7c31adb20d5eee314233abfe48515cf3')
        self.assertEqual(results[187:], [None] * (1204 - 187))
