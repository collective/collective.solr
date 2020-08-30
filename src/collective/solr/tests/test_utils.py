# -*- coding: utf-8 -*-
from collective.solr.exceptions import SolrConnectionException
from collective.solr.parser import SolrResponse
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING
from collective.solr.tests.utils import getData
from collective.solr.utils import findObjects
from collective.solr.utils import isSimpleSearch
from collective.solr.utils import isSimpleTerm
from collective.solr.utils import isWildCard
from collective.solr.utils import padResults
from collective.solr.utils import prepareData
from collective.solr.utils import prepare_wildcard
from collective.solr.utils import removeSpecialCharactersAndOperators
from collective.solr.utils import setupTranslationMap
from collective.solr.utils import splitSimpleSearch
from unittest import TestCase


class UtilsTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.app = self.layer["app"]
        self.app.manage_addFolder(id="portal", title="Portal")
        self.portal = self.app.portal
        self.portal.manage_addFolder(id="foo", title="Foo")
        self.portal.foo.manage_addFolder(id="bar", title="Bar")
        self.portal.foo.bar.manage_addDocument(id="doc1", title="a document")
        self.portal.foo.bar.manage_addDocument(id="file1", title="a file")
        self.portal.manage_addFolder(id="bar", title="Bar")
        self.portal.bar.manage_addFolder(id="foo", title="Foo")
        self.portal.bar.foo.manage_addDocument(id="doc2", title="a document")
        self.portal.bar.foo.manage_addDocument(id="file2", title="a file")
        self.good = (
            "bar",
            "bar/foo",
            "bar/foo/doc2",
            "bar/foo/file2",
            "foo",
            "foo/bar",
            "foo/bar/doc1",
            "foo/bar/file1",
        )

    def ids(self, results):
        return tuple(sorted([r[0] for r in results]))

    def testZopeFindAndApply(self):
        found = self.app.ZopeFindAndApply(self.portal, search_sub=True)
        self.assertEqual(self.ids(found), self.good)

    def testFindObjects(self):
        found = list(findObjects(self.portal))
        # the starting point itself is returned
        self.assertEqual(found[0], ("", self.portal))
        # but the rest should be the same...
        self.assertEqual(self.ids(found[1:]), self.good)

    def testSimpleTerm(self):
        self.assertTrue(isSimpleTerm("foo"))
        self.assertTrue(isSimpleTerm("foo "))
        self.assertTrue(isSimpleTerm(u"føø"))
        self.assertTrue(isSimpleTerm("føø"))
        self.assertFalse(isSimpleTerm("foo!"))
        self.assertFalse(isSimpleTerm('"foo"'))
        self.assertFalse(isSimpleTerm(u"føø!"))
        # XXX Why would this be false?
        # self.assertFalse(isSimpleTerm(six.text_type('föö', 'latin')))
        self.assertTrue(isSimpleTerm("foo42"))
        self.assertTrue(isSimpleTerm("42foo"))
        self.assertFalse(isSimpleTerm("foo bar"))
        self.assertFalse(isSimpleTerm("42 foo"))

    def testSimpleSearch(self):
        self.assertTrue(isSimpleSearch("foo"))
        self.assertTrue(isSimpleSearch("foo bar"))
        self.assertTrue(isSimpleSearch("foo bar "))
        self.assertTrue(isSimpleSearch("foo   bar"))
        self.assertTrue(isSimpleSearch(u"føø bär"))
        self.assertTrue(isSimpleSearch("føø bär"))
        self.assertTrue(isSimpleSearch("foo*"))
        self.assertTrue(isSimpleSearch("foo* bar*"))
        self.assertTrue(isSimpleSearch("*foo*"))
        self.assertTrue(isSimpleSearch('"foo"'))
        self.assertTrue(isSimpleSearch('"foo bar"'))
        self.assertTrue(isSimpleSearch('"foo AND bar"'))
        self.assertTrue(isSimpleSearch('foo "AND" bar'))
        self.assertTrue(isSimpleSearch('"foo" "bar"'))
        self.assertTrue(isSimpleSearch("fo?bar"))
        self.assertTrue(isSimpleSearch("foo bar?"))
        self.assertTrue(
            isSimpleSearch(
                "areallyverylongword " "andanotherreallylongwordwithsomecake"
            )
        )
        self.assertTrue(
            isSimpleSearch(
                "areallyverylongword " "andanotherreallylongwordwithsomecake *"
            )
        )
        self.assertFalse(isSimpleSearch(""))
        self.assertFalse(isSimpleSearch(u"føø bär!"))
        # XXX Why would this be false?
        # self.assertFalse(isSimpleSearch(six.text_type('föö bär', 'latin')))
        self.assertFalse(isSimpleSearch("foo AND bar"))
        self.assertFalse(isSimpleSearch("foo OR bar"))
        self.assertFalse(isSimpleSearch("foo NOT bar"))
        self.assertFalse(isSimpleSearch('"foo" OR bar'))
        self.assertFalse(isSimpleSearch("(foo OR bar)"))
        self.assertFalse(isSimpleSearch("+foo"))
        self.assertFalse(isSimpleSearch("name:foo"))
        self.assertFalse(isSimpleSearch("foo && bar"))
        self.assertTrue(isSimpleSearch("2000"))
        self.assertTrue(isSimpleSearch("foo 2000"))
        self.assertFalse(isSimpleSearch("foo 1/2000"))
        self.assertTrue(isSimpleSearch("foo 42 bar11"))
        self.assertTrue(isSimpleSearch("2000 foo"))

    def testSplitSimpleSearch(self):
        self.assertEqual(splitSimpleSearch("foo bar"), ["foo", "bar"])
        self.assertEqual(
            splitSimpleSearch('foo "bar foobar" baz'), ["foo", '"bar foobar"', "baz"]
        )
        self.assertRaises(AssertionError, splitSimpleSearch, "foo AND bar")
        self.assertEqual(splitSimpleSearch("foo 42"), ["foo", "42"])

    def testIsWildCard(self):
        self.assertTrue(isWildCard("foo*"))
        self.assertTrue(isWildCard("fo?"))
        self.assertTrue(isWildCard("fo?o"))
        self.assertTrue(isWildCard("fo*oo"))
        self.assertTrue(isWildCard("fo?o*"))
        self.assertTrue(isWildCard("*foo"))
        self.assertTrue(isWildCard("*foo*"))
        self.assertTrue(isWildCard("foo* bar"))
        self.assertTrue(isWildCard("foo bar?"))
        self.assertTrue(isWildCard("*"))
        self.assertTrue(isWildCard("?"))
        self.assertTrue(isWildCard(u"føø*"))
        self.assertTrue(isWildCard(u"føø*".encode("utf-8")))
        self.assertTrue(isWildCard(u"*føø*"))
        self.assertFalse(isWildCard("foo"))
        self.assertFalse(isWildCard("fo#o"))
        self.assertFalse(isWildCard("foo bar"))
        self.assertFalse(isWildCard(u"føø"))
        self.assertFalse(isWildCard(u"føø".encode("utf-8")))
        # other characters might be meaningful in solr, but we don't
        # distinguish them properly (yet)
        self.assertFalse(isWildCard("foo#?"))

    def testPrepareWildcard(self):
        self.assertEqual(prepare_wildcard("Foo"), "foo")
        self.assertEqual(prepare_wildcard("and"), "and")
        self.assertEqual(prepare_wildcard("or"), "or")
        self.assertEqual(prepare_wildcard("not"), "not")
        self.assertEqual(prepare_wildcard("Foo and bar"), "foo and bar")
        self.assertEqual(prepare_wildcard("Foo AND Bar"), "foo AND bar")
        self.assertEqual(prepare_wildcard("FOO AND NOT BAR"), "foo AND NOT bar")
        self.assertEqual(prepare_wildcard("Foo OR Bar"), "foo OR bar")
        self.assertEqual(prepare_wildcard("FOO OR NOT BAR"), "foo OR NOT bar")
        self.assertEqual(
            prepare_wildcard("FOO AND BAR OR FOO AND NOT BAR"),
            "foo AND bar OR foo AND NOT bar",
        )

    def test_removeSpecialCharactersAndOperators(self):
        special = [
            "AND",
            "OR",
            "NOT",
            "+",
            "-",
            "&",
            "|",
            "!",
            "(",
            ")",
            "{",
            "}",
            "[",
            "]",
            "^",
            "~",
            "*",
            "?",
            ":",
            "\\",
            "/",
            "]",
        ]
        for character_or_operant in special:
            self.assertEqual(
                removeSpecialCharactersAndOperators(
                    "%s text %s text %s"
                    % (character_or_operant, character_or_operant, character_or_operant)
                ),
                "  text   text  ",
                "Character not removed: %s" % character_or_operant,
            )

    def test_solr_exception(self):
        e = SolrConnectionException(503, "Error happend", "<xml></xml>")

        def test_raise():
            raise e

        self.assertRaisesRegexp(
            SolrConnectionException, "HTTP code=503, reason=Error happend", test_raise
        )
        self.assertEqual(
            repr(e), "HTTP code=503, Reason=Error happend, body=<xml></xml>"
        )


class TranslationTests(TestCase):
    def testTranslationMap(self):
        tm = setupTranslationMap()
        self.assertEqual("\f\a\b".translate(tm), " " * 3)
        self.assertEqual("foo\nbar".translate(tm), "foo\nbar")
        self.assertEqual("foo\n\tbar\a\f\r".translate(tm), "foo\n\tbar  \r")

    def testRemoveControlCharacters(self):
        data = {"SearchableText": "foo\n\tbar\a\f\r"}
        prepareData(data)
        self.assertEqual(data, {"SearchableText": "foo\n\tbar  \r"})

    def testUnicodeSearchableText(self):
        data = {"SearchableText": u"f\xf8\xf8 bar"}
        prepareData(data)
        self.assertEqual(data, {"SearchableText": u"f\xf8\xf8 bar"})


class BatchingHelperTests(TestCase):
    def results(self):
        xml_response = getData("quirky_response.txt")
        response = SolrResponse(xml_response)
        return response.response  # the result set is named 'response'

    def testResult(self):
        results = self.results()
        self.assertEqual(results.numFound, "1204")
        self.assertEqual(len(results), 137)
        self.assertEqual(results[0].UID, "7c31adb20d5eee314233abfe48515cf3")

    def testResultsPadding(self):
        results = self.results()
        padResults(results)
        self.assertEqual(len(results), 1204)
        self.assertEqual(results[0].UID, "7c31adb20d5eee314233abfe48515cf3")
        self.assertEqual(results[137:], [None] * (1204 - 137))

    def testResultsPaddingWithStart(self):
        results = self.results()
        padResults(results, start=50)
        self.assertEqual(len(results), 1204)
        self.assertEqual(results[:50], [None] * 50)
        self.assertEqual(results[50].UID, "7c31adb20d5eee314233abfe48515cf3")
        self.assertEqual(results[187:], [None] * (1204 - 187))
