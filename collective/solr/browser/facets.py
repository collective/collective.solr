from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import SearchBoxViewlet


class SearchBox(SearchBoxViewlet):
    index = ViewPageTemplateFile('searchbox.pt')


class SearchFacetsView(BrowserView):
    """ view for displaying facetting info as provided by solr searches """

