from copy import deepcopy
from operator import itemgetter
from time import time

import six
from collective.solr.interfaces import IFacetTitleVocabularyFactory
from collective.solr.utils import isActive
from plone import api
from plone.app.contentlisting.interfaces import IContentListing
from plone.app.layout.viewlets.common import SearchBoxViewlet
from plone.base.batch import Batch
from plone.memoize.volatile import cache
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.browser.search import Search
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.ZCTextIndex.ParseTree import ParseError
from six.moves.urllib.parse import urlencode
from zope.component import getUtility, queryUtility
from zope.i18n import translate
from zope.i18nmessageid import Message


def param(view, name):
    """return a request parameter as a list"""
    value = view.request.form.get(name, [])
    if isinstance(value, six.string_types):
        value = [value]
    return value


def facetParameters(view):
    """determine facet fields to be queried for"""
    marker = []
    fields = view.request.get("facet.field", view.request.get("facet_field", marker))
    if isinstance(fields, six.string_types):
        fields = [fields]
    if fields is marker:
        fields = getattr(view, "facet_fields", marker)
    if fields is marker:
        fields = getattr(view.context, "facet_fields", marker)
    if fields is marker:
        registry = getUtility(IRegistry)
        fields = registry["collective.solr.facets"]
    dependencies = {}
    for idx, field in enumerate(fields):
        if ":" in field:
            facet, dep = [f.strip() for f in field.split(":", 1)]
            dependencies[facet] = [d.strip() for d in dep.split(",")]
    return fields, dependencies


def convertFacets(fields, view, filter=None):
    """convert facet info to a form easy to process in templates"""
    info = []
    params = view.request.form.copy()
    if "b_start" in params:
        del params["b_start"]  # Clear the batch when limiting a result set
    facets, dependencies = list(facetParameters(view))
    params["facet.field"] = facets = list(facets)
    fq = params.get("fq", [])
    if isinstance(fq, six.string_types):
        fq = params["fq"] = [fq]
    selected = set([facet.split(":", 1)[0] for facet in fq])
    for field, values in fields.items():
        counts = []
        vfactory = queryUtility(IFacetTitleVocabularyFactory, name=field)
        if vfactory is None:
            # Use the default fallback
            vfactory = getUtility(IFacetTitleVocabularyFactory)
        vocabulary = vfactory(view.context)

        sorted_values = sorted(list(values.items()), key=itemgetter(1), reverse=True)
        for name, count in sorted_values:
            p = deepcopy(params)
            p.setdefault("fq", []).append(('%s:"%s"' % (field, name)).encode("utf-8"))
            if field in p.get("facet.field", []):
                p["facet.field"].remove(field)
            if filter is None or filter(name, count):
                title = name
                if name in vocabulary:
                    title = vocabulary.getTerm(name).title
                if isinstance(title, Message):
                    title = translate(title, context=view.request)
                counts.append(
                    dict(
                        name=name,
                        count=count,
                        title=title,
                        query=urlencode(p, doseq=True),
                    )
                )
        deps = dependencies.get(field, None)
        visible = deps is None or selected.intersection(deps)
        if counts and visible:
            info.append(dict(title=field, counts=counts, name=name))
    if facets:  # sort according to given facets (if available)

        def pos(item):
            try:
                return facets.index(item)
            except ValueError:
                return len(facets)  # position the item at the end

        sortkey = pos
    else:  # otherwise sort by title
        sortkey = itemgetter("title")
    return sorted(info, key=sortkey)


class FacetMixin:
    """mixin with helpers common to the viewlet and view"""

    hidden = ViewPageTemplateFile("templates/hiddenfields.pt")

    def hiddenfields(self):
        """render hidden fields suitable for inclusion in search forms"""
        facets, dependencies = facetParameters(self)
        queries = param(self, "fq")
        # don't break on empty lines in registry field
        return self.hidden(facets=filter(None, facets), queries=queries)


class SearchBox(SearchBoxViewlet, FacetMixin):

    # template must be registered here for the test to work
    index = ViewPageTemplateFile("templates/searchbox.pt")


def _query_cache_key(method, self, query):
    """Hash the query dict, and cache for one minute"""
    return (
        hash("::".join([f"{k}={query[k]}" for k in sorted(query.keys())])),
        time() // 60,
    )


class SearchView(Search):

    @property
    def solr_active(self):
        return isActive()

    def search_facets(self):
        view = api.content.get_view("search-facets", self.context, self.request)
        return view(results=self.all_results())

    @cache(_query_cache_key)
    def caching_results(self, query):
        catalog = getToolByName(self.context, "portal_catalog")
        return catalog(**query)

    def all_results(self):
        """To extract factes we need to disable batching and contentlisting"""
        query = self.filter_query({})
        if "b_start" in query:
            del query["b_start"]
        if "b_size" in query:
            del query["b_size"]
        if not query:
            return []
        return self.caching_results(query)

    def results(
        self, query=None, batch=True, b_size=10, b_start=0, use_content_listing=True
    ):
        """Bypass .results() in a way that leverages memoized all_results"""
        if not self.solr_active:
            return super().results(b_start=b_start, b_size=b_size)

        b_start = int(b_start)
        b_size = 10
        results = self.all_results()
        results = IContentListing(results)
        results = Batch(results, b_size, b_start)
        return results


class SearchFacetsView(BrowserView, FacetMixin):
    """view for displaying facetting info as provided by solr searches"""

    def __call__(self, results):
        self.results = results
        return self.index()

    def facets(self):
        """prepare and return facetting info for the given SolrResponse"""
        fcs = getattr(self.results, "facet_counts", None)
        if self.results is not None and fcs is not None:
            filter = lambda name, count: name and count > 0
            return convertFacets(fcs.get("facet_fields", {}), self, filter)
        else:
            return None

    def selected(self):
        """determine selected facets and prepare links to clear them;
        this assumes that facets are selected using filter queries"""
        info = []
        facets = param(self, "facet.field")
        fq = param(self, "fq")
        for idx, query in enumerate(fq):
            field, value = query.split(":", 1)
            params = self.request.form.copy()
            params["fq"] = fq[:idx] + fq[idx + 1 :]
            if field not in facets:
                params["facet.field"] = facets + [field]
            if value.startswith('"') and value.endswith('"'):
                # Look up a vocabulary to provide a title for this facet
                vfactory = queryUtility(IFacetTitleVocabularyFactory, name=field)
                if vfactory is None:
                    # Use the default fallback
                    vfactory = getUtility(IFacetTitleVocabularyFactory)
                vocabulary = vfactory(self.context)
                value = value[1:-1]
                if value in vocabulary:
                    value = vocabulary.getTerm(value).title
                if isinstance(value, Message):
                    value = translate(value, context=self.request)

                info.append(
                    dict(title=field, value=value, query=urlencode(params, doseq=True))
                )
        return info
