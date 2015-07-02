# -*- coding: utf-8 -*-
import json

from plone.app.search.browser import Search as PloneAppSearchBrowserView
from Products.CMFCore.utils import getToolByName


class Search(PloneAppSearchBrowserView):

    def __call__(self):
        """If Accept header is 'application/json' or the URL contains
           'format=json', the @@search view will return a JSON response.
           Otherwise we just return the standard plone.app.search view.
        """
        json_header = self.request.response.getHeader(
            'Accept'
        ) == 'application/json'
        json_format = self.request.get('format') == 'json'
        if json_header or json_format:
            self.request.response.setHeader(
                'Content-Type',
                'application/json; charset=utf-8'
            )
            SearchableText = self.request.get('SearchableText')
            result = []
            if SearchableText:
                catalog = getToolByName(self.context, 'portal_catalog')
                result = [
                    {
                        'id': x.id,
                        'portal_type': x.portal_type,
                        'title': x.Title,
                        'description': x.description,
                        'url': x.getURL(),
                    }
                    for x in catalog(SearchableText=SearchableText)
                ]
            return json.dumps(result, indent=2, sort_keys=True)
        return super(PloneAppSearchBrowserView, self).__call__()
