defaultOperator
---------------

In Solr 7, the defaultOperator (AND, OR) are gone.
The operator needs to be explicitly set for every query with the q.op parameter.
For collective.solr < 7, the default operator was a configuration parameter of the buildout recipe.
For now, we hard-coded the q.op parameter for every query that collective solr sends:

https://github.com/collective/collective.solr/blob/7.x/src/collective/solr/search.py#L62

It would be an option to make the default query parameter configurable in the Solr control panel in Plone.
Though, the Solr developers made an argument that the operator is specific to each query and nothing that you should set globally:

https://issues.apache.org/jira/browse/SOLR-2724
https://lucene.apache.org/solr/guide/7_0/major-changes-in-solr-7.html


Solr Core
---------

Calls to solr now always require a core.
Before Solr 7 it was possible to call http://localhost:8983/solr/admin/ping.
Those call are no longer possible and will fail with a 404.
Solr 7 requires to use a core:

http://localhost:8983/solr/plone/admin/ping.

The default core in collective.solr is called "/plone".


wt=true (XML is not the default any longer)
indent=on (default?)
lowercaseOperators=true
q.op=AND (no default operator any longer)

sow=true (split on whitespace, not default to true any longer)

NEW:

(Pdb) normalize(output.get(skip=1))
[
    'POST /solr/select HTTP/1.1\nHost: localhost\n
    Accept-Encoding: identity\n
    Content-Length: 106\n
    Content-Type: application/x-www-form-urlencoded; charset=utf-8\n
    \n
    rows=10',
    'fl=%2A+score',
    'indent=on',
    'lowercaseOperators=true',
    'q.op=AND',
    'q=%2Bid%3A%5B%2A+TO+%2A%5D',
    'sow=true',
    'wt=xml']

OLD:

(Pdb) normalize(request)
[
    'POST /solr/select HTTP/1.1\n
    Host: localhost\n
    Accept-Encoding: identity\n
    Content-Length: 64\n
    Content-Type: application/x-www-form-urlencoded; charset=utf-8\n
    \n
    q=%2Bid%3A%5B%2A+TO+%2A%5D',
    'fl=%2A+score',
    'indent=on',
    'rows=10',
    'wt=xml'
  ]


New params for search method (lowercase_operator, default_operator, sow):

    def search(self, query, wt='xml', sow='true', lowercase_operator='true',
               default_operator='AND', **parameters):

There is no default search field in Solr 7 any longer.
