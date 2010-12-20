collective.solr
===============

Introduction
------------

`collective.solr`_ is an approach to integrate the `Solr`_ search engine with
`Plone`_.  It provides an indexing processor for use with
`collective.indexing`_ as well as a search API similar to the standard portal
catalog.  `GenericSetup`_ profiles can be applied to set up content indexing
in `Solr`_ and use it as a backend for `Plone`_'s site and live search
facilities.

  .. _`collective.solr`: http://plone.org/products/collective.solr/
  .. _`collective.indexing`: http://plone.org/products/collective.indexing/
  .. _`Solr`: http://lucene.apache.org/solr/
  .. _`Plone`: http://www.plone.org/
  .. _`GenericSetup`: http://www.zope.org/Products/GenericSetup/


Current Status
--------------

The code is used in production in many sites and considered stable. This
add-on can be installed in a `Plone`_ 4.x site to enable indexing operations
as well as searching (site and live search) using `Solr`_. Doing so will not
only significantly improve search performance - especially for a large number
of indexed objects, but also reduce the memory footprint of your `Plone`_
instance by allowing to remove the ``SearchableText`` index from the portal
catalog - at least for most sites. A sample buildout_ is provided for your
convenience.

  .. _buildout: http://svn.plone.org/svn/collective/collective.solr/trunk/buildout.cfg

For outstanding issues and features remaining to be implemented please see the
`to-do list`__ included in the package as well as it's `issue tracker`__.

  .. __: http://svn.plone.org/svn/collective/collective.solr/trunk/TODO.txt
  .. __: http://plone.org/products/collective.solr/issues


Installation
------------

The following buildout configuration may be used to get started quickly::

  [buildout]
  extends =
    buildout.cfg
    http://svn.plone.org/svn/collective/collective.solr/trunk/buildout/solr-1.4.cfg

  [instance]
  eggs += collective.solr

After saving this to let's say ``solr.cfg`` buildout can be run and the
`Solr`_ server and `Plone`_ instance started::

  $ python bootstrap.py
  $ bin/buildout -c solr.cfg
  ...
  $ bin/solr-instance start
  $ bin/instance start

Next the "collective.solr (site search)" profile should be applied via the
portal setup or when creating a fresh Plone site.  After activating and
configuring the integration in the Plone control panel and initially indexing
any existing content using the provided maintenance view:

  http://localhost:8080/plone/@@solr-maintenance/reindex

facet information should appear in Plone's search results page.


FAQs / Troubleshooting
----------------------

**"AssertionError: cannot use multiple direct indexers; please enable queueing"**

  Symptom
    When activating additional add-ons or applying a GenericSetup profile
    you get the following error::

      AssertionError: cannot use multiple direct indexers; please enable queueing
  Problem
    Early versions of the add-on used a persistent local utility, which is
    still present in your ZODB.  This utility has meanwhile been replaced so
    that there are currently two instances present.  However, without queued
    indexing being enabled, only one such indexer is allowed at a time.
  Solution
    Please re-install the add-on via the quick installer Zope Management
    Interface. Note that this will reset all your configuration but won't
    change any data in Solr.


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
  .. __: http://svn.plone.org/svn/collective/collective.solr/trunk/buildout/solr.cfg


Credits
-------

This code was inspired by `enfold.solr`_ by `Enfold Systems`_ as well as `work
done at the snowsprint'08`__.  The `solr.py` module is based on the original
python integration package from `Solr`_ itself.

Development was kindly sponsored by `Elkjop`_ and the
`Nordic Council and Nordic Council of Ministers`_.

  .. _`enfold.indexing`: https://svn.enfoldsystems.com/browse/public/enfold.solr/branches/snowsprint08-buildout/enfold.indexing/
  .. _`enfold.solr`: https://svn.enfoldsystems.com/browse/public/enfold.solr/branches/snowsprint08-buildout/enfold.solr/
  .. _`Enfold Systems`: http://www.enfoldsystems.com/
  .. __: http://tarekziade.wordpress.com/2008/01/20/snow-sprint-report-1-indexing/
  .. _`Elkjop`: http://www.elkjop.no/
  .. _`Nordic Council and Nordic Council of Ministers`: http://www.norden.org/en/
