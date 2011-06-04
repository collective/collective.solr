Introduction
------------

collective.solr integrates the `Solr`_ search engine with `Plone`_.

Apache Solr is based on Lucene and is *the* enterprise open source search
engine. It powers the search of sites like Twitter, the Apple and iTunes Stores,
Wikipedia, Netflix and many more.

Solr does not only scale to any level of content, but provides rich search
functionality, like facetting, geospatial search, suggestions, spelling
corrections, indexing of binary formats and a whole variety of powerful tools to
configure custom search solutions. It has integrated clustering and
load-balancing to provide a high level of robustness.

collective.solr comes with a default configuration and setup of Solr that makes
it extremely easy to get started, yet provides a vastly superior search quality
compared to Plone's integrated text search based on ZCTextIndex.


Current Status
--------------

The code is used in production in many sites and considered stable. This
add-on can be installed in a `Plone`_ 4.x site to enable indexing operations
as well as searching (site and live search) using `Solr`_. Doing so will not
only significantly improve search quality and performance - especially for a
large number of indexed objects, but also reduce the memory footprint of your
`Plone`_ instance by allowing to remove the ``SearchableText`` and
``Description`` indexes from the catalog.


Installation
------------

The following buildout configuration may be used to get started quickly::

  [buildout]
  extends =
    buildout.cfg
    https://github.com/Jarn/collective.solr/raw/master/buildout/solr.cfg

  [instance]
  eggs += collective.solr

After saving this to let's say ``solr.cfg`` the buildout can be run and the
`Solr`_ server and `Plone`_ instance started::

  $ python bootstrap.py
  $ bin/buildout -c solr.cfg
  ...
  $ bin/solr-instance start
  $ bin/instance start

Next you should activate the ``collective.solr (site search)`` add-on in the
add-on control panel of Plone. After activation you should review the settings
in the new ``Solr Settings`` control panel. To index all your content in Solr
you can call the provided maintenance view:

  http://localhost:8080/plone/@@solr-maintenance/reindex


FAQs / Troubleshooting
----------------------

**Searches only return up to 10 results**

  Symptom
    Searches don't display `more than 10 results`__ even though there are
    more matches and "Maximum search results" is set to "0" (to always return
    all results).
  Problem
    With the default setting for "Maximum search results" (i.e. "0") no
    `rows`_ parameter is included when sending queries to Solr.  This results
    in Solr's default setting to be applied, and both its internal default
    (when removing the parameter from `solrconfig.xml`) as well as the
    "max-num-results" option in `collective.recipe.solrinstance`__ end up
    with a value of 10.
  Solution
    Please update your buildout to use a higher setting for "max-num-results".
    It should be higher than or equal to the maximum number of total search
    results you'd like to get from your site.  The `sample configuration`__
    uses a value of "1000".

  .. __: http://plone.org/products/collective.solr/issues/20
  .. _`rows`: http://wiki.apache.org/solr/CommonQueryParameters#rows
  .. __: http://pypi.python.org/pypi/collective.recipe.solrinstance/
  .. __: https://github.com/Jarn/collective.solr/raw/master/buildout/solr.cfg


Development
-----------

Releases can be found on the Python Package Index at
http://pypi.python.org/pypi/collective.solr. The code and issue trackers can be
found on GitHub at https://github.com/Jarn/collective.solr.

For outstanding issues and features remaining to be implemented please see the
`to-do list`__ included in the package as well as it's `issue tracker`__.

  .. __: https://github.com/Jarn/collective.solr/blob/master/TODO.txt
  .. __: https://github.com/Jarn/collective.solr/issues


Credits
-------

This code was inspired by `enfold.solr`_ by `Enfold Systems`_ as well as `work
done at the snowsprint'08`__.  The `solr.py` module is based on the original
python integration package from `Solr`_ itself.

Development was kindly sponsored by `Elkjop`_ and the
`Nordic Council and Nordic Council of Ministers`_.

  .. _`enfold.solr`: https://svn.enfoldsystems.com/trac/public/browser/enfold.solr/branches/snowsprint08-buildout/enfold.solr
  .. _`Enfold Systems`: http://www.enfoldsystems.com/
  .. __: http://tarekziade.wordpress.com/2008/01/20/snow-sprint-report-1-indexing/
  .. _`Elkjop`: http://www.elkjop.no/
  .. _`Nordic Council and Nordic Council of Ministers`: http://www.norden.org/en/
  .. _`Solr`: http://lucene.apache.org/solr/
  .. _`Plone`: http://www.plone.org/
