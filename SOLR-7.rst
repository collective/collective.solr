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
