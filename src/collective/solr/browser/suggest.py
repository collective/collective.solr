import json
import urllib

from collective.solr.interfaces import ISolrConnectionManager
from Products.Five.browser import BrowserView
from zope.component import getUtility


class SuggestView(BrowserView):
    """Get autocomplete suggestions using solr's suggester component."""

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
        response = connection.doPost(
            connection.solrBase + '/suggest?' + params, '', {})
        results = json.loads(response.read())
        spellcheck = results.get('spellcheck', None)
        if not spellcheck:
            return json.dumps(suggestions)
        spellcheck_suggestions = spellcheck.get('suggestions', None)
        if not spellcheck_suggestions:
            return json.dumps(suggestions)

        for suggestion in spellcheck_suggestions[1]['suggestion']:
            suggestions.append(dict(label=suggestion, value=suggestion))

        return json.dumps(suggestions)
