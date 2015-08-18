# -*- coding: utf-8 -*-
from collective.solr.dispatcher import solrSearchResults
from collective.solr.interfaces import ISolrConnectionManager
from plone.app.search.browser import Search as PloneAppSearchBrowserView
from Products.Five.browser import BrowserView
from zope.component import getUtility

import json
import urllib


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
                        'description': x.description,
                        'url': x.getURL(),
                        'expires': x.expires.ISO8601(),
                        'effective': x.effective.ISO8601(),
                        'created': x.created.ISO8601(),
                        'modified': x.modified.ISO8601(),
                        'creator': x.Creator,
                        'review_state': x.review_state,
                    }
                    for x in solr_search.results()
                ]
                if getattr(solr_search, 'spellcheck', False):
                    if solr_search.spellcheck.get('suggestions'):
                        result['suggestions'] = solr_search.spellcheck.get(
                            'suggestions'
                        )
            return json.dumps(result, indent=2, sort_keys=True)
        return super(PloneAppSearchBrowserView, self).__call__()


class AutocompleteView(BrowserView):

    def __call__(self):
        term = self.request.get('term', '')
        if not term:
            return json.dumps([])
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()

        if connection is None:
            return json.dumps([])

        params = {}
        params['q'] = term
        params['wt'] = 'json'

        params = urllib.urlencode(params, doseq=True)
        response = connection.doGet(
            connection.solrBase + '/autocomplete?' + params, {})
        results = json.loads(response.read())

        if 'grouped' not in results:
            return json.dumps([])

        groups = results.get('grouped')['autocomplete']['groups']

        suggestions = [
            x['doclist']['docs'][0]['autocomplete'] for x in groups
        ]

        result = []
        for suggestion in suggestions:
            result.append(dict(label=suggestion, value=suggestion))

        return json.dumps(result)
