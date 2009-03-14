from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import SearchBoxViewlet


class SearchBox(SearchBoxViewlet):
    index = ViewPageTemplateFile('searchbox.pt')


class SearchFacetsView(BrowserView):
    """ view for displaying facetting info as provided by solr searches """

    def __call__(self, *args, **kw):
        self.args = args
        self.kw = kw
        return super(SearchFacetsView, self).__call__(*args, **kw)

    def facets(self):
        """ prepare and return facetting info for the given SolrResponse """
        results = self.kw.get('results', None)
        if results is None:
            return []
        return 'facets foo here!'
