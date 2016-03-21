Indexing binary documents
*************************

At this point collective.solr uses Plone's default capabilities to index binary documents.
It does so via `portal_transforms` and installing command line tools like `wv2` or `pdftotext`.
Work is under way to expose and use the `Apache Tika`_ Solr integration available via the `update/extract` handler.

Once finished this will speed up indexing of binary documents considerably,
as the extraction will happen out-of-process on the Solr server side.
`Apache Tika`_ also supports a much larger list of formats than can be supported by adding external command line tools.

There is room for more improvements in this area,
as collective.solr will still send the binary data to Solr as part of the end-user request/transaction.
To further optimize this,
Solr index operations can be stored in a task queue as provided by `plone.app.async` or solutions build on top of `Celery`.
This is currently outside the scope of `collective.solr`.

.. _`Apache Tika`: http://tika.apache.org/
