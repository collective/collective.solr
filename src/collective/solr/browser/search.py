# -*- coding: utf-8 -*-
from collective.solr.dispatcher import solrSearchResults
from plone.app.search.browser import Search as PloneAppSearchBrowserView

import json


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
            result = {
                'data': [],
                'suggestions': [],
            }
            if SearchableText:
                solr_search = solrSearchResults(
                    SearchableText=SearchableText,
                    spellcheck='true',
                    use_solr='true',
                )
                result['data'] = [
                    {
                        'id': x.id,
                        'portal_type': x.portal_type,
                        'title': x.Title,
                        'description': x.get('description', u''),
                        'url': x.getURL(),
                    }
                    for x in solr_search.results()
                ]
                result['suggestions'] = self.extract_suggestions(
                    solr_search.spellcheck
                )
            return json.dumps(result, indent=2, sort_keys=True)
        return super(PloneAppSearchBrowserView, self).__call__()

    def extract_suggestions(self, result):
        return result
