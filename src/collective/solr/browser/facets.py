# -*- coding: utf-8 -*-
from copy import deepcopy
from operator import itemgetter
from six.moves.urllib.parse import urlencode

from plone.app.layout.viewlets.common import SearchBoxViewlet
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.component import queryUtility
from zope.i18n import translate
from zope.i18nmessageid import Message

from collective.solr.interfaces import IFacetTitleVocabularyFactory
from plone.registry.interfaces import IRegistry
import six


def param(view, name):
    """ return a request parameter as a list """
    value = view.request.form.get(name, [])
    if isinstance(value, six.string_types):
        value = [value]
    return value


def facetParameters(view):
    """ determine facet fields to be queried for """
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
    """ convert facet info to a form easy to process in templates """
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
    """ mixin with helpers common to the viewlet and view """

    hidden = ViewPageTemplateFile("hiddenfields.pt")

    def hiddenfields(self):
        """ render hidden fields suitable for inclusion in search forms """
        facets, dependencies = facetParameters(self)
        queries = param(self, "fq")
        return self.hidden(facets=facets, queries=queries)


class SearchBox(SearchBoxViewlet, FacetMixin):

    index = ViewPageTemplateFile("searchbox.pt")


class SearchFacetsView(BrowserView, FacetMixin):
    """ view for displaying facetting info as provided by solr searches """

    def __call__(self, *args, **kw):
        self.args = args
        self.kw = kw
        return super(SearchFacetsView, self).__call__(*args, **kw)

    def facets(self):
        """ prepare and return facetting info for the given SolrResponse """
        results = self.kw.get("results", None)
        fcs = getattr(results, "facet_counts", None)
        if results is not None and fcs is not None:
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
