# -*- coding: utf-8 -*-
import json
import urllib

from collective.solr.interfaces import ISolrConnectionManager
from Products.Five.browser import BrowserView
from zope.component import getUtility


class SuggestView(BrowserView):

    def __call__(self):
        suggestions = []
        term = self.request.get('term', '')
        if not term:
            return json.dumps(suggestions)
        manager = getUtility(ISolrConnectionManager)
        connection = manager.getConnection()

        if connection is None:
            return json.dumps(suggestions)

        params = {}
        params['q'] = term
        params['wt'] = 'json'

        params = urllib.urlencode(params, doseq=True)
        response = connection.doGet(
            connection.solrBase + '/spell?' + params, {})
        results = json.loads(response.read())

        # Check for spellcheck
        spellcheck = results.get('spellcheck', None)
        if not spellcheck:
            return json.dumps(suggestions)

        # Check for existing spellcheck suggestions
        spellcheck_suggestions = spellcheck.get('suggestions', None)
        correctly_spelled = \
            spellcheck_suggestions == [u'correctlySpelled', True]

        # Autocomplete
        if correctly_spelled:
            return json.dumps(
                [x['Title'] for x in results['response']['docs']])

        if not spellcheck_suggestions:
            return json.dumps(suggestions)

        # Collect suggestions
        if spellcheck_suggestions[1]:
            for suggestion in spellcheck_suggestions[1]['suggestion']:
                suggestions.append(dict(label=suggestion, value=suggestion))

        return json.dumps(suggestions)


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
        url = connection.solrBase + '/autocomplete?' + params
        response = connection.doGet(url, {})
        results = json.loads(response.read())

        if 'grouped' not in results:
            return json.dumps([])

        groups = results.get('grouped')['title_autocomplete']['groups']

        suggestions = [
            x['doclist']['docs'][0]['title_autocomplete'] for x in groups
        ]

        result = []
        for suggestion in suggestions:
            result.append(dict(label=suggestion, value=suggestion))
        return json.dumps(result)
