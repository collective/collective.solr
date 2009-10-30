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

The implementation is considered to be nearly finished. The package can be
installed in a `Plone`_ 3.x site to enable indexing operations as well as
searching (site and live search) using `Solr`_. Doing so will not only
significantly improve search performance |---| especially for a large number
of indexed objects, but also reduce the memory footprint of your `Plone`_
instance by allowing to remove the ``SearchableText`` index from the portal
catalog |---| at least for most sites. A sample buildout_ is provided for your
convenience.

  .. |--| unicode:: U+2013   .. en dash
  .. |---| unicode:: U+2014  .. em dash
  .. _buildout: http://svn.plone.org/svn/collective/collective.solr/trunk/buildout.cfg

The code was written with emphasis on minimalism, clarity and maintainability.
It comes with extensive tests covering the code base. The package is currently
in use in production and considered stable.

  .. at more than 95%.  XXX: make coverage run pick up all modules!

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
    http://svn.plone.org/svn/collective/collective.solr/trunk/buildout/solr-1.3.cfg

  [instance]
  eggs += collective.solr
  zcml += collective.solr

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
    When installing additional packages or applying a GenericSetup profile
    you're getting the following error::

      AssertionError: cannot use multiple direct indexers; please enable queueing
  Problem
    Early versions of the package used a persistent local utility, which is
    still present in your ZODB.  This utility has meanwhile been replaced so
    that there are currently two instances present.  However, without queued
    indexing being enabled, only one such indexer is allowed at a time.
  Solution
    Please simply re-install the package via Plone's control panel or the
    quick-installer.  Alternatively you can also use the ZMI "Components" tab
    on your site root object, typically located at
    http://localhost:8080/plone/manage_components, to remove the broken
    utilities from the XML.  Search for "broken".


Credits
-------

This code was inspired by `enfold.solr`_ by `Enfold Systems`_ as well as `work
done at the snowsprint'08`__.  The `solr.py` module is based on the original
python integration package from `Solr`_ itself.

Development was kindly sponsored by `Elkjop`_.

  .. _`enfold.indexing`: https://svn.enfoldsystems.com/browse/public/enfold.solr/branches/snowsprint08-buildout/enfold.indexing/
  .. _`enfold.solr`: https://svn.enfoldsystems.com/browse/public/enfold.solr/branches/snowsprint08-buildout/enfold.solr/
  .. _`Enfold Systems`: http://www.enfoldsystems.com/
  .. __: http://tarekziade.wordpress.com/2008/01/20/snow-sprint-report-1-indexing/
  .. _`Elkjop`: http://www.elkjop.no/

