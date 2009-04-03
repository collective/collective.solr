from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import SearchBoxViewlet
from collective.solr.browser.utils import facetParameters, convertFacets
from urllib import urlencode


def param(view, name):
    """ return a request parameter as a list """
    value = view.request.form.get(name, [])
    if isinstance(value, basestring):
        value = [value]
    return value


class SearchBox(SearchBoxViewlet):

    index = ViewPageTemplateFile('searchbox.pt')

    def available(self):
        """ determine facet fields to be queried for """
        return facetParameters(self.context, self.request)

    def queries(self):
        """ return filter queries used in the current request """
        return param(self, 'fq')


class SearchFacetsView(BrowserView):
    """ view for displaying facetting info as provided by solr searches """

    def __call__(self, *args, **kw):
        self.args = args
        self.kw = kw
        return super(SearchFacetsView, self).__call__(*args, **kw)

    def queries(self):
        """ return filter queries used in the current request """
        return param(self, 'fq')

    def available(self):
        """ determine facet fields to be queried for """
        return facetParameters(self.context, self.request)

    def facets(self):
        """ prepare and return facetting info for the given SolrResponse """
        results = self.kw.get('results', None)
        fcs = getattr(results, 'facet_counts', None)
        if results is not None and fcs is not None:
            return convertFacets(fcs['facet_fields'],
                self.context, self.request.form)
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
