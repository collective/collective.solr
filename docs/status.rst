Current Status
==============

The code is used in production in many sites and considered stable.
This add-on can be installed in a `Plone`_ 4.1 (or later) site to enable indexing operations as well as searching (site and live search) using `Solr`_.
Doing so will not only significantly improve search quality and performance -
especially for a large number of indexed objects,
but also reduce the memory footprint of your `Plone`_ instance by allowing you to remove the ``SearchableText``, ``Description`` and ``Title`` indexes from the catalog.
In large sites with 100000 content objects and more,
searches using ``ZCTextIndex`` often taken 10 seconds or more and require a good deal of memory from ZODB caches.
Solr will typically answer these requests in 10ms to 50ms at which point network latency and the rendering speed of Plone's page templates are a more dominant factor.

  .. _`Solr`: http://lucene.apache.org/solr/
  .. _`Plone`: http://www.plone.org/
