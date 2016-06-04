TODOs:
------

* Migrate tests to use plone.app.testing
* Migrate control panel to use plone.autoform and plone.app.registry
* support for date facets
* result iterator (with __len__ on results object)
* support for "navtree" and "level" arguments for path queries
* provide decorator for solr exceptions
* add signal handlers (see store.py)
* add a configurable queue limit for large transactions
* mapping from accessor name to attribute name, i.e. getTitle -> title,
  preferably via <copyField> tags in the solr schema
* evaluate http://www.gnuenterprise.org/~jcater/solr.py as a replacement
  (also see http://tinyurl.com/2zcogf)
* evaluate sunburnet as a replacement https://pypi.python.org/pypi/sunburnt
* evaluate mysolr as backend https://pypi.python.org/pypi/mysolr
* implement LocalParams to have a nicer facet view http://wiki.apache.org/solr/SimpleFacetParameters#Multi-Select_Faceting_and_LocalParams
* Use current search view and get rid of ancient search override
* Implement a push only and read only mode
* Play nice with eea.facetednavigation
