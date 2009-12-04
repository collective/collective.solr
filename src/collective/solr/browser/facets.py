from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import queryUtility
from plone.app.layout.viewlets.common import SearchBoxViewlet
from collective.solr.interfaces import ISolrConnectionConfig
from urllib import urlencode
from copy import deepcopy
from string import strip


def param(view, name):
    """ return a request parameter as a list """
    value = view.request.form.get(name, [])
    if isinstance(value, basestring):
        value = [value]
    return value


def facetParameters(context, request):
    """ determine facet fields to be queried for """
    marker = []
    fields = request.get('facet.field', request.get('facet_field', marker))
    if isinstance(fields, basestring):
        fields = [fields]
    if fields is marker:
        fields = getattr(context, 'facet_fields', marker)
    if fields is marker:
        config = queryUtility(ISolrConnectionConfig)
        if config is not None:
            fields = config.facets
    dependencies = {}
    for idx, field in enumerate(fields):
        if ':' in field:
            facet, dep = map(strip, field.split(':', 1))
            dependencies[facet] = map(strip, dep.split(','))
    return fields, dependencies


def convertFacets(fields, context=None, request={}, filter=None):
    """ convert facet info to a form easy to process in templates """
    info = []
    params = request.copy()   # request needs to be a dict, i.e. request.form
    facets, dependencies = list(facetParameters(context, request))
    params['facet.field'] = facets = list(facets)
    fq = params.get('fq', [])
    if isinstance(fq, basestring):
        fq = params['fq'] = [fq]
    selected = set([facet.split(':', 1)[0] for facet in fq ])
    for field, values in fields.items():
        counts = []
        second = lambda a, b: cmp(b[1], a[1])
        for name, count in sorted(values.items(), cmp=second):
            p = deepcopy(params)
            p.setdefault('fq', []).append('%s:"%s"' % (field, name.encode('utf-8')))
            if field in p.get('facet.field', []):
                p['facet.field'].remove(field)
            if filter is None or filter(name, count):
                counts.append(dict(name=name, count=count,
                    query=urlencode(p, doseq=True)))
        deps = dependencies.get(field, None)
        visible = deps is None or selected.intersection(deps)
        if counts and visible:
            info.append(dict(title=field, counts=counts))
    if facets:          # sort according to given facets (if available)
        def pos(item):
            try:
                return facets.index(item)
            except ValueError:
                return len(facets)      # position the item at the end
        func = lambda a, b: cmp(pos(a), pos(b))
    else:               # otherwise sort by title
        func = lambda a, b: cmp(a['title'], b['title'])
    return sorted(info, cmp=func)


class FacetMixin:
    """ mixin with helpers common to the viewlet and view """

    hidden = ViewPageTemplateFile('hiddenfields.pt')

    def hiddenfields(self):
        """ render hidden fields suitable for inclusion in search forms """
        facets, dependencies = facetParameters(self.context, self.request)
        queries = param(self, 'fq')
        return self.hidden(facets=facets, queries=queries)


class SearchBox(SearchBoxViewlet, FacetMixin):

    index = ViewPageTemplateFile('searchbox.pt')


class SearchFacetsView(BrowserView, FacetMixin):
    """ view for displaying facetting info as provided by solr searches """

    def __call__(self, *args, **kw):
        self.args = args
        self.kw = kw
        return super(SearchFacetsView, self).__call__(*args, **kw)

    def facets(self):
        """ prepare and return facetting info for the given SolrResponse """
        results = self.kw.get('results', None)
        fcs = getattr(results, 'facet_counts', None)
        if results is not None and fcs is not None:
            filter = lambda name, count: name and count > 0
            return convertFacets(fcs.get('facet_fields', {}),
                self.context, self.request.form, filter)
        else:
            return None

    def selected(self):
        """ determine selected facets and prepare links to clear them;
            this assumes that facets are selected using filter queries """
        info = []
        facets = param(self, 'facet.field')
        fq = param(self, 'fq')
        for idx, query in enumerate(fq):
            field, value = query.split(':', 1)
            params = self.request.form.copy()
            params['fq'] = fq[:idx] + fq[idx+1:]
            if field not in facets:
                params['facet.field'] = facets + [field]
            info.append(dict(title=field, value=value,
                query=urlencode(params, doseq=True)))
        return info
