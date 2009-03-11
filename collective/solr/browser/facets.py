from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.layout.viewlets.common import SearchBoxViewlet


class SearchBox(SearchBoxViewlet):
    index = ViewPageTemplateFile('searchbox.pt')
