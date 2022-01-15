from unittest import TestCase

from collective.solr.browser.facets import SearchBox, SearchFacetsView
from collective.solr.browser.interfaces import IThemeSpecific
from collective.solr.dispatcher import solrSearchResults
from collective.solr.exceptions import SolrConnectionException
from collective.solr.testing import (
    LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING,
    activateAndReindex,
)
from collective.solr.utils import activate
from plone import api
from plone.app.testing import TEST_USER_ID, setRoles
from zope.component import getMultiAdapter
from zope.interface import alsoProvides


class SolrFacettingTests(TestCase):
    layer = LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        activateAndReindex(self.portal)
        response = self.request.RESPONSE
        self.write = response.write
        response.write = lambda x: x  # temporarily ignore output
        self.maintenance = self.portal.unrestrictedTraverse("solr-maintenance")

    def tearDown(self):
        self.request.RESPONSE.write = self.write
        activate(active=False)

    def _create_uf(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        if "Members" not in self.portal:
            mf = api.content.create(self.portal, "Folder", id="Members")
        else:
            mf = self.portal["Members"]
        if TEST_USER_ID not in mf:
            uf = api.content.create(mf, "Folder", id=TEST_USER_ID)
        else:
            uf = mf[TEST_USER_ID]
            api.content.transition(obj=mf, transition="hide")
            api.content.transition(obj=uf, transition="hide")
        self.maintenance.reindex()
        setRoles(self.portal, TEST_USER_ID, [])

    def testFacettedSearchWithKeywordArguments(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Event", id="event1", title="Welcome")
        self.maintenance.reindex()
        results = solrSearchResults(
            SearchableText="Welcome", facet="true", facet_field="portal_type"
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ["/plone/event1", "/plone/front-page"],
        )
        types = results.facet_counts["facet_fields"]["portal_type"]
        self.assertEqual(types["Document"], 1)
        self.assertEqual(types["Event"], 1)

    def testFacettedSearchWithRequestArguments(self):
        self._create_uf()
        self.request = self.layer["request"]
        self.request.form["SearchableText"] = "News"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = "review_state"
        results = solrSearchResults(self.request)
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ["/plone/news", "/plone/news/aggregator"],
        )
        states = results.facet_counts["facet_fields"]["review_state"]
        self.assertEqual(states, dict(private=0, published=2))

    def testMultiFacettedSearch(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Event", id="event1", title="Welcome")
        self.maintenance.reindex()
        results = solrSearchResults(
            SearchableText="Welcome",
            facet="true",
            facet_field=["portal_type", "review_state"],
        )
        self.assertEqual(
            sorted([r.path_string for r in results]),
            ["/plone/event1", "/plone/front-page"],
        )
        facets = results.facet_counts["facet_fields"]
        self.assertEqual(facets["portal_type"]["Event"], 1)
        self.assertEqual(facets["review_state"]["published"], 1)

    def testFacettedSearchWithFilterQuery(self):
        self._create_uf()
        self.request = self.layer["request"]
        self.request.form["SearchableText"] = "News"
        self.request.form["fq"] = "portal_type:Collection"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = "review_state"
        results = solrSearchResults(self.request)
        self.assertEqual([r.path_string for r in results], ["/plone/news/aggregator"])
        states = results.facet_counts["facet_fields"]["review_state"]
        self.assertEqual(states, dict(private=0, published=1))

    def testFacettedSearchWithDependencies(self):
        # facets depending on others should not show up initially
        self.request.form["SearchableText"] = "News"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = ["portal_type", "review_state:portal_type"]
        view = SearchFacetsView(self.portal, self.request)
        view.kw = dict(results=solrSearchResults(self.request))
        facets = [facet["title"] for facet in view.facets()]
        self.assertEqual(facets, ["portal_type"])
        # now again with the required facet selected
        self.request.form["fq"] = "portal_type:Collection"
        view.kw = dict(results=solrSearchResults(self.request))
        facets = [facet["title"] for facet in view.facets()]
        self.assertEqual(facets, ["portal_type", "review_state"])

    def testFacettedSearchWithUnicodeFilterQuery(self):
        self.portal.news.portal_type = "Føø"
        self.maintenance.reindex()
        self.request.form["SearchableText"] = "News"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = "portal_type"
        view = SearchFacetsView(self.portal, self.request)
        view.kw = dict(results=solrSearchResults(self.request))
        facets = view.facets()
        self.assertEqual(
            sorted([c["name"] for c in facets[0]["counts"]]), ["Collection", u"Føø"]
        )

    def checkOrder(self, html, *order):
        for item in order:
            position = html.find(item)
            self.assertTrue(
                position >= 0, 'menu item "%s" missing or out of order' % item
            )
            html = html[position:]

    def testFacetsInformationView(self):
        setRoles(self.portal, TEST_USER_ID, ["Manager"])
        self.portal.invokeFactory("Event", id="event1", title="Welcome")
        self.maintenance.reindex()
        self.request.form["SearchableText"] = "Welcome"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = "portal_type"
        alsoProvides(self.request, IThemeSpecific)
        view = getMultiAdapter((self.portal, self.request), name="search-facets")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        results = solrSearchResults(self.request)
        output = view(results=results)
        self.checkOrder(
            output, "portal-searchfacets", "Content type", "Document", "1", "Event", "1"
        )

    def testFacetFieldsInSearchBox(self):
        self.request = self.portal.REQUEST
        viewlet = SearchBox(self.portal, self.request, None, None)
        if hasattr(viewlet, "__of__"):
            viewlet = viewlet.__of__(self.portal)
        viewlet.update()
        output = viewlet.render()
        self.checkOrder(
            output,
            "<input",
            'name="facet" value="true"',
            "<input",
            'value="portal_type"',
            "<input",
            'value="review_state"',
            "</form>",
        )
        # try overriding the desired facets in the self.request
        self.request.form["facet.field"] = ["foo"]
        output = viewlet.render()
        self.checkOrder(
            output,
            "<input",
            'name="facet" value="true"',
            "<input",
            'value="foo"',
            "</form>",
        )
        self.assertFalse("portal_type" in output)

    def testUnknownFacetField(self):
        self.request.form["SearchableText"] = "News"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = "foo"
        alsoProvides(self.request, IThemeSpecific)
        self.assertRaises(SolrConnectionException, solrSearchResults, self.request)

    def testNoFacetFields(self):
        self.request.form["SearchableText"] = "News"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = []
        alsoProvides(self.request, IThemeSpecific)
        view = getMultiAdapter((self.portal, self.request), name="search-facets")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        output = view(results=solrSearchResults(self.request))
        self.assertFalse("portal-searchfacets" in output, output)

    def testEmptyFacetValue(self):
        # let's artificially create an empty value;  while this is a
        # somewhat unrealistic scenario, empty values may very well occur
        # for additional custom indexes...
        self.portal.news.portal_type = ""
        self.maintenance.reindex()
        # after updating the solr index the view can be checked...
        self.request.form["SearchableText"] = "News"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = "portal_type"
        alsoProvides(self.request, IThemeSpecific)
        view = getMultiAdapter((self.portal, self.request), name="search-facets")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        results = solrSearchResults(self.request)
        output = view(results=results)
        # the empty facet value should be displayed resulting in
        # only one list item (`<dd>`)
        self.assertEqual(len(output.split("<dd>")), 2)
        # let's also make sure there are no empty filter queries
        self.assertFalse("fq=portal_type%3A&amp;" in output)

    def testFacetOrder(self):
        self.request.form["SearchableText"] = "News"
        self.request.form["facet"] = "true"
        self.request.form["facet_field"] = ["portal_type", "review_state"]
        alsoProvides(self.request, IThemeSpecific)
        view = getMultiAdapter((self.portal, self.request), name="search-facets")
        if hasattr(view, "__of__"):
            view = view.__of__(self.portal)
        results = solrSearchResults(self.request)
        output = view(results=results)
        # the displayed facets should match the given order...
        self.checkOrder(output, "portal-searchfacets", "Content type", "Review state")
        # let's also try the other way round...
        self.request.form["facet_field"] = ["review_state", "portal_type"]
        results = solrSearchResults(self.request)
        output = view(results=results)
        self.checkOrder(output, "portal-searchfacets", "Review state", "Content type")
