====================================================
collective.solr - Solr integration for the Plone CMS
====================================================

.. image:: https://secure.travis-ci.org/collective/collective.solr.png?branch=master
    :target: http://travis-ci.org/collective/collective.solr

.. image:: https://coveralls.io/repos/collective/collective.solr/badge.png?branch=master
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

ZCTextIndex Replacement
***********************



Detailed Documentation
======================

A full Documentation of the Solr integration of Plone could be found in `docs.plone.org collective.solr`_.

.. _`docs.plone.org collective.solr`: http://docs.plone.org/external/collective.solr/docs/index.html


Installation & Configuration
============================

The following buildout configuration may be used to get started quickly::

  [buildout]
  extends =
    buildout.cfg
    https://github.com/collective/collective.solr/raw/master/solr.cfg
    https://github.com/collective/collective.solr/raw/master/solr-5.2.x.cfg # or any other version of Solr 

  [instance]
  eggs += collective.solr


After saving this to let's say ``solr.cfg`` the buildout can be run and the `Solr`_ server and `Plone`_ instance started::

  $ python bootstrap-buildout.py
  $ bin/buildout -c solr.cfg
  ...
  $ bin/solr-instance start
  $ bin/instance start

Next you should activate the ``collective.solr (site search)`` add-on in the add-on control panel of Plone.
After activation you should review the settings in the new ``Solr Settings`` control panel.
To index all your content in Solr you can call the provided maintenance view::

  http://localhost:8080/plone/@@solr-maintenance/reindex

Note that the example ``solr.cfg`` is bound to change. Always copy the file to your local buildout. In general you should never rely on extending buildout config files from servers that aren't under your control.


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

The code is used in production in many sites and considered stable. This add-on can be installed in a `Plone`_ 4.1 (or later) site to enable indexing operations as well as searching (site and live search) using `Solr`_. Doing so will not only significantly improve search quality and performance - especially for a large number of indexed objects, but also reduce the memory footprint of your `Plone`_ instance by allowing you to remove the ``SearchableText``, ``Description`` and ``Title`` indexes from the catalog.
In large sites with 100000 content objects and more, searches using ``ZCTextIndex`` often taken 10 seconds or more and require a good deal of memory from ZODB caches. Solr will typically answer these requests in 10ms to 50ms at which point network latency and the rendering speed of Plone's page templates are a more dominant factor.


Bug Reporting & Development
===========================

Releases can be found on the Python Package Index at http://pypi.python.org/pypi/collective.solr. The code and issue trackers can be found on GitHub at https://github.com/collective/collective.solr.

For outstanding issues and features remaining to be implemented please see the `issue tracker`__.

  .. __: https://github.com/collective/collective.solr/issues

  .. _`Solr`: http://lucene.apache.org/solr/
  .. _`Plone`: http://www.plone.org/
