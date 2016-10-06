====================================================
collective.solr - Solr integration for the Plone CMS
====================================================

.. image:: https://secure.travis-ci.org/collective/collective.solr.svg?branch=master
    :target: http://travis-ci.org/collective/collective.solr

.. image:: https://coveralls.io/repos/collective/collective.solr/badge.svg?branch=master
    :target: https://coveralls.io/r/collective/collective.solr

.. image:: https://img.shields.io/pypi/dm/collective.solr.svg
    :target: https://pypi.python.org/pypi/collective.solr/
    :alt: Downloads

.. image:: https://img.shields.io/pypi/v/collective.solr.svg
    :target: https://pypi.python.org/pypi/collective.solr/
    :alt: Latest Version

.. image:: https://img.shields.io/pypi/status/collective.solr.svg
    :target: https://pypi.python.org/pypi/collective.solr/
    :alt: Egg Status

.. image:: https://img.shields.io/pypi/l/collective.solr.svg
    :target: https://pypi.python.org/pypi/collective.solr/
    :alt: License


.. contents::
    :depth: 1


``collective.solr`` integrates the `Solr`_ search engine with `Plone`_.

Apache Solr is based on Lucene and is *the* enterprise open source search engine. It powers the search of sites like Twitter, the Apple and iTunes Stores, Wikipedia, Netflix and many more.

Solr does not only scale to any level of content, but provides rich search functionality, like faceting, geospatial search, suggestions, spelling corrections, indexing of binary formats and a whole variety of powerful tools to configure custom search solutions. It has integrated clustering and load-balancing to provide a high level of robustness.

``collective.solr`` comes with a default configuration and setup of Solr that makes it extremely easy to get started, yet provides a vastly superior search quality compared to Plone's integrated text search based on ``ZCTextIndex``.


Features
========

Solr Features
-------------

* Schema and Schemaless Configuration
* Information Retrieval System
* Speed (in comparission to ZCTextIndex)


Features of Solr Integration into Plone
---------------------------------------

Search Enhancements
*******************

* Facets
* Indexing of binary documents
* Spellchecking / suggestions
* Wildcard searches
* Exclude from search
* Elevation


Detailed Documentation
======================

A full Documentation of the Solr integration of Plone could be found on `collectivesolr.readthedocs.org`_.

.. _`collectivesolr.readthedocs.org`: http://collectivesolr.readthedocs.org/en/latest/


Installation & Configuration
============================

Download the latest default Solr configuration from github::

  $ wget https://github.com/collective/collective.solr/raw/master/solr.cfg
  $ wget https://raw.githubusercontent.com/collective/collective.solr/master/solr-4.10.x.cfg

.. note: Please do not extend your buildout directly with those files since they are likely to change over time. Always fetch the files via wget to have a stable local copy. In general you should never rely on extending buildout config files from servers that aren't under your control.

Extend your buildout to use those files and make sure collective.solr is added
to the eggs in your instance section. Your full buildout file should look
something like this::

  [buildout]
  parts += instance
  extends =
      http://dist.plone.org/release/4.3.8/versions.cfg
      solr.cfg
      solr-4.10.x.cfg

  [instance]
  recipe = plone.recipe.zope2instance
  http-address = 8080
  user = admin:admin
  eggs =
      Plone
      collective.solr

  [versions]
  collective.recipe.solrinstance = 5.3.2

After saving this to let's say ``buildout.cfg`` the buildout can be run and the `Solr`_ server and `Plone`_ instance started::

  $ python bootstrap-buildout.py
  $ bin/buildout
  ...
  $ bin/solr-instance start
  $ bin/instance start

Next you should activate the ``collective.solr (site search)`` add-on in the add-on control panel of Plone.
After activation you should review the settings in the new ``Solr Settings`` control panel.
To index all your content in Solr you can call the provided maintenance view::

  http://localhost:8080/plone/@@solr-maintenance/reindex


Solr connection configuration in ZCML
-------------------------------------

The connections settings for Solr can be configured in ZCML and thus in buildout. This makes it easier when copying databases between multiple Zope instances with different Solr servers.

Example::

    zcml-additional =
        <configure xmlns:solr="http://namespaces.plone.org/solr">
            <solr:connection host="localhost" port="8983" base="/solr/plone"/>
       </configure>


Current Project Status
======================

The code is used in production in many sites and considered stable. This add-on can be installed in a `Plone`_ 4.1 (or later) site to enable indexing operations as well as searching (site and live search) using `Solr`_. Doing so will not only significantly improve search quality and performance - especially for a large number of indexed objects, but also reduce the memory footprint of your `Plone`_ instance by allowing you to remove the ``SearchableText``, ``Description`` and ``Title`` indexes from the catalog as well as the lexicons if no other indexes are using them.

In large sites with 100000 content objects and more, searches using ``ZCTextIndex`` often taken 10 seconds or more and require a good deal of memory from ZODB caches. Solr will typically answer these requests in 10ms to 50ms at which point network latency and the rendering speed of Plone's page templates are a more dominant factor.


Bug Reporting & Development
===========================

Releases can be found on the Python Package Index at http://pypi.python.org/pypi/collective.solr. The code and issue trackers can be found on GitHub at https://github.com/collective/collective.solr.

For outstanding issues and features remaining to be implemented please see the `issue tracker`__.

  .. __: https://github.com/collective/collective.solr/issues

  .. _`Solr`: http://lucene.apache.org/solr/
  .. _`Plone`: http://www.plone.org/
