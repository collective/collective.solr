# -*- coding: UTF-8 -*-
from zope.component import getUtility
from collective.solr.browser.errors import ErrorView
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from zope.component import getMultiAdapter

import json
import six
import unittest


class MockResponse:
    def read(self):
        result = {
            "responseHeader": {"status": 0, "QTime": 4},
            "response": {"numFound": 0, "start": 0, "docs": []},
            "spellcheck": {
                "suggestions": [
                    "Plane",
                    {
                        "numFound": 1,
                        "startOffset": 0,
                        "endOffset": 5,
                        "origFreq": 0,
                        "suggestion": [{"word": "Plone", "freq": 13}],
                    },
                    "correctlySpelled",
                    False,
                    "collation",
                    [
                        "collationQuery",
                        "Plone",
                        "hits",
                        0,
                        "misspellingsAndCorrections",
                        ["Plane", "Plone"],
                    ],
                ]
            },
        }
        return json.dumps(result)


class MockConnection:

    solrBase = "/solr/plone"

    def doPost(self, url, foo, bar):
        return MockResponse()

    def doGet(self, url, bar):
        return MockResponse()


class MockSolrConnectionManager:
    def getConnection(self):
        return MockConnection()


class SuggestTermsViewIntegrationTest(unittest.TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.request["ACTUAL_URL"] = self.portal.absolute_url()
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        # Unregister standard SolrConnectionManager
        self.gsm = self.portal.getSiteManager()
        config = getUtility(ISolrConnectionManager)
        self.gsm.unregisterUtility(component=config, provided=ISolrConnectionManager)

    def test_suggest_terms_view_is_registered(self):
        try:
            getMultiAdapter((self.portal, self.request), name="suggest-terms")
        except:  # noqa
            self.fail("suggest-terms view is not registered properly.")

    def test_suggest_terms_view_without_param(self):
        view = getMultiAdapter((self.portal, self.portal.REQUEST), name="suggest-terms")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        self.failUnless(view())
        self.assertEqual(view(), "[]")

    def test_suggest_terms_view_with_empty_param(self):
        self.request.set("term", "")
        view = getMultiAdapter((self.portal, self.portal.REQUEST), name="suggest-terms")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        self.failUnless(view())
        self.assertEqual(view(), "[]")

    def test_suggest_terms_view_with_param_not_in_solf(self):
        self.request.set("term", "abcdef")
        view = getMultiAdapter((self.portal, self.portal.REQUEST), name="suggest-terms")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        self.failUnless(view())
        self.assertEqual(view(), "[]")

    def test_suggest_terms_view_with_correctly_spelled_param(self):
        self.request.set("term", "Plone")
        view = getMultiAdapter((self.portal, self.portal.REQUEST), name="suggest-terms")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        self.failUnless(view())
        self.assertEqual(view(), "[]")

    def test_suggest_terms_view_with_incorrectly_spelled_param(self):
        # Replace SolrConnectionManager with Mock
        self.gsm.registerUtility(MockSolrConnectionManager(), ISolrConnectionManager)
        self.assertTrue(getUtility(ISolrConnectionManager))
        self.request.set("term", "Plane")
        view = getMultiAdapter((self.portal, self.portal.REQUEST), name="suggest-terms")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        self.failUnless(view())
        output = json.loads(view())
        self.assertEqual(len(output), 1)
        self.assertEqual(set(output[0]["value"].keys()), set(["word", "freq"]))
        self.assertEqual(output[0]["value"]["word"], "Plone")
        self.assertEqual(output[0]["value"]["freq"], 13)
        self.assertEqual(set(output[0]["label"].keys()), set(["word", "freq"]))
        self.assertEqual(output[0]["label"]["word"], "Plone")
        self.assertEqual(output[0]["label"]["freq"], 13)


class AutoCompleteTest(unittest.TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]

    def test_autocomplete_noterm(self):
        ac = self.portal.restrictedTraverse("solr-autocomplete")
        self.assertEqual(json.loads(ac()), [])

    def test_autocomplete_emptyterm(self):
        self.request.form["term"] = ""
        ac = self.portal.restrictedTraverse("solr-autocomplete")
        self.assertEqual(json.loads(ac()), [])


class TestErrorView(unittest.TestCase):
    def test_error_view(self):
        request = {}
        try:
            raise OSError("Test Exception")
        except Exception as e:
            view = ErrorView(e, request)
        if six.PY2:
            expected_error = "<type 'exceptions.OSError"
        else:
            expected_error = "OSError"
        self.assertEqual(
            view.errorInfo(), {"type": expected_error, "value": ("Test Exception",)}
        )
