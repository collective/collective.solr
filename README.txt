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
  .. _buildout: http://svn.plone.org/svn/collective/collective.solr/buildout

The code was written with emphasis on minimalism, clarity and maintainability.
It comes with extensive tests covering the code base. The package is currently
in use in production and considered stable.

  .. at more than 95%.  XXX: make coverage run pick up all modules!

For outstanding issues and features remaining to be implemented please see the
`to-do list`__ included in the package.

  .. __: http://svn.plone.org/svn/collective/collective.solr/trunk/TODO.txt


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

