Indexing binary documents
*************************

Collective.solr uses Plone's default capabilities to index NamedFileBlob fields, if they are declared searchable via plone.app.dexterity.textindexer.
It does so via `portal_transforms` and installing command line tools like `wv2` or `pdftotext`.

File and Image objects use the `Apache Tika`_ Solr integration available via the `update/extract` handler.

The Tika extraction happens out-of-process on the Solr server side.
`Apache Tika`_ also supports a much larger list of formats than can be supported by adding external command line tools.

Note that you have to enable remote streaming for this to work.
Note that you also have to configure the Java security policy to be allowed to access the blobstorage,
if you have the ``use_tika`` setting configured to ``False`` (which means: use filesystem not network access).
These security settings can be made by providing the proper environment variables to the solr script, for example::

  SOLR_ENABLE_REMOTE_STREAMING=true SOLR_ENABLE_STREAM_BODY=true SOLR_OPTS="-Dsolr.allowPaths=/path/to/your.buildout/var/blobstorage" bin/solr-foreground

If you are using buildout to configure supervisord, you can achieve this by adding the following to your buildout config::

  [supervisor]
  supervisord-environment = SOLR_ENABLE_REMOTE_STREAMING=true,SOLR_ENABLE_STREAM_BODY=true,SOLR_OPTS="-Dsolr.allowPaths=${instance:blob-storage}"

Note that the buildout environment is comma separated, while the actual shell command is space separated.

There is room for more improvements in this area,
as collective.solr will still send the binary data to Solr as part of the end-user request/transaction.
To further optimize this,
Solr index operations can be stored in a task queue as provided by `plone.app.async` or solutions build on top of `Celery`.
This is currently outside the scope of `collective.solr`.

.. _`Apache Tika`: https://tika.apache.org/
