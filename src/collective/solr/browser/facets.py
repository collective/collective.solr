from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import SearchBoxViewlet
from collective.solr.browser.utils import facetParameters, convertFacets


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
