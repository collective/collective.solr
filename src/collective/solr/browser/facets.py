from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import SearchBoxViewlet
from collective.solr.browser.utils import facetParameters, convertFacets
from urllib import urlencode


class SearchBox(SearchBoxViewlet):

    index = ViewPageTemplateFile('searchbox.pt')

    def facets(self):
        """ determine facet fields to be queried for """
        return facetParameters(self.context, self.request)


class SearchFacetsView(BrowserView):
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
            return convertFacets(fcs['facet_fields'],
                self.context, self.request.form)
        else:
            return None

    def selected(self):
        """ determine selected facets and prepare links to clear them;
            this assumes that facets are selected using filter queries """
        info = []
        facets = self.request.form.get('facet.field', [])
        if isinstance(facets, basestring):
            facets = [facets]
        fq = self.request.form.get('fq', [])
        if isinstance(fq, basestring):
            fq = [fq]
        for idx, query in enumerate(fq):
            field, value = query.split(':', 1)
            params = self.request.form.copy()
            params['fq'] = fq[:idx] + fq[idx+1:]
            if field not in facets:
                params['facet.field'] = facets + [field]
            info.append(dict(title=field, query=urlencode(params, doseq=True)))
        return info
