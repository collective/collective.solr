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


Architecture
------------

When working with Solr it's good to keep some things about it in mind.

Solr is not transactional aware or supports any kind of rollback or undo. We
therefor only sent data to Solr at the end of any successful request. This is
done via collective.indexing, a transaction manager and a end request
transaction hook. This means you won't see any changes done to content inside a
request when doing Solr searches later on in the same request. Inside tests you
need to either commit real transactions or otherwise flush the Solr connection.

Solr is not a real time search engine. While there's work under way to make Solr
capable of delivering real time results, there's currently always a certain
delay from the time data is sent to Solr to when it is available in searches.

Search results are returned in Solr by distinct search threads. These search
threads hold a great number of caches which are crucial for Solr to perform.
When index or unindex operations are sent to Solr, it will keep those in memory
until a commit is executed on its own search index. When a commit occurs, all
search threads and thus all caches are thrown away and new threads are created
reflecting the data after the commit. While there's a certain amount of cache
data that is copied to the new search threads, this data has to be validated
against the new index which takes some time. The `useColdSearcher` and
`maxWarmingSearchers` options of the Solr recipe relate to the aspect. While
cache data is copied over and validated for a new search thread, it's `warming`
up. If that process is not yet completed the thread is considered to be `cold`.

In order to get real good performance out of Solr, we need to minimize the
number of commits against the Solr index. We can achieve this by turning off
`auto-commit` and instead use `commitWithin`. So we don't sent a `commit`
to Solr at the end of each index/unindex request on the Plone side. Instead we
tell Solr to commit the data to its index at most after a certain time interval.
Values of 15 minutes to 1 minute work well for this interval. The larger you
can make this interval, the better the performance of Solr will be, at the cost
of search results lagging behind a bit. In this setup we also need to configure
the `autoCommitMaxTime` option of the Solr server, as `commitWithin` only works
for index but not unindex operations. Otherwise a large number of unindex
operations without any index operations occurring could not be reflected in the
index for a long time.

As a result of all the above, the Solr index and the Plone site will always have
slightly diverging contents. If you use Solr to do searches you need to be aware
of this, as you might get results for objects that no longer exist. So any
`brain/getObject` call on the Plone side needs to have error handling code
around it as the object might not be there anymore and traversing to it throws
an exception.

When adding new or deleting old content or changing the workflow state of it,
you will also not see those actions reflected in searches right away, but only
after a delay of at most the `commitWithin` interval. After a `commitWithin`
operation is sent to Solr, any other operations happening during that time
window will be executed after the first interval is over. So with a 15 minute
interval, if document A is indexed at 5:15, B at 5:20 and C at 5:35, both A & B
will be committed at 5:30 and C at 5:50.


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
