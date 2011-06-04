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
`Plone`_ instance by allowing you to remove the ``SearchableText``,
``Description`` and ``Title`` indexes from the catalog. In large sites with
100000 content objects and more, searches using ZCTextIndex often taken 10
seconds or more and require a good deal of memory from ZODB caches. Solr will
typically answer these requests in 10ms to 50ms at which point network latency
and the rendering speed of Plone's page templates are a more dominant factor.


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

When working with Solr it's good to keep some things about it in mind. This
information is targeted at developers and integrators trying to use and extend
Solr in their Plone projects.

Indexing
********

Solr is not transactional aware or supports any kind of rollback or undo. We
therefor only sent data to Solr at the end of any successful request. This is
done via collective.indexing, a transaction manager and a end request
transaction hook. This means you won't see any changes done to content inside a
request when doing Solr searches later on in the same request. Inside tests you
need to either commit real transactions or otherwise flush the Solr connection.
There's no transaction concept, so one request doing a search might get some
results in its beginning, than a different request might add new information to
Solr. If the first request is still running and does the same search again it
might get different results taking the changes from the second request into
account.

Solr is not a real time search engine. While there's work under way to make Solr
capable of delivering real time results, there's currently always a certain
delay up to some minutes from the time data is sent to Solr to when it is
available in searches.

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

Searching
*********

Information retrieval is a complex science. We try to give a very brief
explanation here, refer to the literature and documentation of Lucene/Solr for
much more detailed information.

If you do searches in normal Plone, you have a search term and query the
SearchableText index with it. The SearchableText is a simple concentration of
all searchable fields, by default title, description and the body text.

The default ZCTextIndex in Plone uses a simplified version of the Okapi BM25
algorithm described in papers in 1998. It uses two metrics to score documents:

- Term frequency: How often does a search term occur in a document
- Inverse document frequency: The inverse of in how many documents a term
  occurs. Terms only occurring in a few documents are scored higher than those
  occurring in many documents.

It calculates the sum of all scores, for every term common to the query and any
document. So for a query with two terms, a document is likely to score higher
if it contains both terms, except if one of them is a very common term and the
other document contains the non-common term more often.

The similarity function used in Solr/Lucene uses a different algorithm, based on
a combination of a boolean and vector space model, but taking the same
underlying metrics into account. In addition to the term frequency and inverse
document frequency Solr respects some more metrics:

- length normalization: The number of all terms in a field. Shorter fields
  contribute higher scores compared to long fields.
- boost values: There's a variety of boost values that can be applied, both
  index-time document boost values as well as boost values per search field or
  search term

In its pre 2.0 versions, collective.solr used a naive approach and mirrored the
approach taken by ZCTextIndex. So it sent each search query as one query and
matched it against the full SearchableText field inside Solr. By doing that Solr
basically used the same algorithm as ZCTextIndex as it only had one field to
match with the entire text in it. The only difference was the use of the length
normalization, so shorter documents ranked higher than those with longer texts.
This actually caused search quality to be worse, as you'd frequently find
folders, links or otherwise rather empty documents. The Okapi BM25
implementation in ZCTextIndex deliberately ignores the document length for that
reason.

In order to get good or better search quality from Solr, we have to query it in
a different way. Instead of concatenating all fields into one big text, we need
to preserve the individual fields and use their intrinsic importance. We get the
main benefit be realizing that matches on the title and description are more
important than matches on the body text or other fields in a document.
collective.solr 2.0+ does exactly that by introducing a `search-pattern` to be
used for text searches. In its default form it causes each query to work against
the title, description and full searchable text fields and boosts the title by
a high and the description by a medium value. The length normalization already
provides an improvement for these fields, as the title is likely short, the
description a bit longer and the full text even longer. By using explicit boost
values the effect gets to be more pronounced.

If you do custom searches or want to include more fields into the full text
search you need to keep the above in mind. Simply setting the `searchable`
attribute on the schema of a field to `True` will only include it in the big
searchable text stream. If you for example include a field containing tags, the
simple tag names will likely 'drown' in the full body text. You might want to
instead change the search pattern to include the field and potentially put a
boost value on it - though it will be more important as it's likely to be
extremely short. Similarly extracting the full text of binary files and simply
appending them into the search stream might not be the best approach. You should
rather index those in a separate field and then maybe use a boost value of less
than one to make the field less important. Given to documents with the same
content, one as a normal page and one as a binary file, you'll likely want to
find the page first, as it's faster to access and read than the file.

There's a good number of other improvements you can do using query time and
index time boost values. To provide index time boost values, you can provide
a skin script called `solr_boost_index_values` which gets the object to be
indexed and the data sent to Solr as arguments and returns a dictionary of field
names to boost values for each document. The safest is to return a boost value
for the empty string, which results in a document boost value. Field level boost
values don't work with all searches, especially wildcard searches as done by
most simple web searches. The index time boost allows you to implement policies
like boosting certain content types over others, taking into account ratings or
number of comments as a measure of user feedback or anything else that can be
derived from each content item.


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
