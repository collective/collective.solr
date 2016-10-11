Changelog
=========

6.0a1 (2016-10-11)
------------------

- Plone 5 compatibility
  [timo, tomgross, sneridagh, gforcada]

- New ReactJS based search UI
  [timo, sneridagh]

- Boost script now available via control panel
  [tomgross]

- Add ignore_exceptions option for Solr reindex. This option is true by
  default when running solr_reindex from the command line.
  [tschorr]


5.0.3 (2016-06-05)
------------------

- Fix Pypi page.
  [timo]


5.0.2 (2016-06-04)
------------------

- Fix README formatting.
  [timo]


5.0.1 (2016-06-04)
------------------

- Fix BlobError occuring when indexing new files (fixes #120)
  [tomgross]

- Make extracting text from binary content and indexing 2 steps (#65)
  [tomgross]

- Make suggest search work when entering multiple search terms.
  [jcharra]

- Fix field-list export.
  [gforcada]


5.0 (2016-04-13)
----------------

Note: This release requires you to to update your Solr config and do a full reindex. Make sure you add "updateLog = true" to your "solr-instance"
buildout section. See https://github.com/collective/collective.solr/blob/master/solr.cfg for a working example.

- Ported atomic updates from ftw.solr.
  This requires you to update your solr config, load the new solr config and
  do a full reindex. For more informations check the "feature" section.
  The feature was implemented in ftw.solr by [lgraf].
  [mathias.leimgruber]

- Add support for using different request handlers in search requests.
  [buchi]

- solr.cfg has been moved from https://github.com/collective/collective.solr/raw/master/buildout/solr.cfg to https://github.com/collective/collective.solr/raw/master/solr.cfg.
  [timo]

- Add configurable SolrLayer for unit testing Solr configuration.
  [timo]

- Make CollectiveSolrLayer configurable, to allow testing different cores.
  [timo]

- Added context to search utility. This allows query to be used in AJAX calls.
  [tomgross]

- Use GET method in spell check request (as it's an idempotent request which
  does not affect server state)
  [reinhardt]

- Add zopectl.command for reindexing. Do not rely on positional arguments in _get_site.
  [tschorr]

- Move inline function out of to the global scope to make it more readable.
  [gforcada]

- Unify all exceptions raised by collective.solr.
  [gforcada]

- Soft commit changes while reindexing.
  This allows to get results on searches while reindexing is taking place.
  [gforcada]


4.1.0 (2015-02-19)
------------------

- Pep8.
  [timo,do3cc]

- Refactor tests. Tests are now based on plone.app.testing. You can now
  use the Fixture COLLECTIVE_SOLR_FIXTURE and the utility method
  collective.solr.testing:activateAndReindex() to test your code with solr
  [do3cc]

- Refactor ISearch. The method buildQuery has been replaced with buildQueryAndParameters.
  Responsabilities have been divided in the search view and the utility, now they are
  all in the search utility. If you used the method before, please analyse
  the changes in collective.solr.dispatcher:solrSearchResults from 4.0.3 to 4.1.0
  You can probably benefit from the changes.
  [do3cc]

- Add "actual_result_count" attribute to SolrResponse to emulate
  catalog attribute.
  [cekk]

- Add browserlayer suport (with upgrade-step)
  [cekk]

- Use public method to get blob path (fixes error on maintenance/reindex also)
  [tomgross]

- Fix UnicodeError in BinaryAdder
  [tomgross]

- Added ignore_portal_types and only_portal_types parameter to reindex for maintenance_view
  [jkubaile]


4.0.3 (2014-06-18)
------------------

- Set logger level for 'failing back to "max_results" from 'info' to 'debug'.
  [timo]


4.0.2 (2014-05-14)
------------------

- Fix typo in Binary Indexer.
  [giacomos]

- Fix typo in facet search.
  [tschorr]

- Add facet title vocabulary factory for review_state.
  [tschorr]

- Add Dexterity support for showinsearch indexer.
  [timo]

- Test agains Solr 4.8.0.
  [timo]


4.0.1 (unreleased)
------------------

- Add support for solr.FloatField.
  [timo]

- Move icon_expr from actionicons.xml to controlpanel.xml to avoid deprecation
  warnings.
  [timo]


4.0 (2014-01-08)
----------------

- Solr 4.x compatibility.
  [timo]

- Don't fail on incorrect date string.
  [tom_gross]

- Fixed index for to datetime and time.
  [Rodrigo]

- Make it work with 'OR' as the default operator in solr.
  [csenger]

- Add `limit` option to `reindex` method of the maintenance view.
  (from 3.0.1 release, was not in 3.1)
  [fschulze]

- Add configuration for solr host, port and base throught zcml. This is
  ported from ftw.solr.
  [csenger, buchi]

- Set max_results param to '10000000' as default value as described in
  http://wiki.apache.org/solr/CommonQueryParameters#rows. It seems this has
  changed in Solr 4.
  [timo]

- Integrate 'suggest-terms' view from ftw.solr. No UI yet!
  [timo, 4teamworks]

- Add plone.app.testing setup.
  [timo]

- Support fuzzy search for SearchableText.
  [csenger,timo]

- Make sure slashes are properly escaped in the search query. Solr 4.0 added
  regular expression support, which means that '/' is now a special character
  and must be escaped if searching for literal forward slash.
  [timo]

- Implement the getDataOrigin method for the FlareContentListingObject that
  plone.app.contentlisting defines and that plone.app.search expects to exist.
  [timo]

- Use tika for extracting binary content.
  [tom_gross]

- Plone 4.3 compatibility of search view
  [tom_gross]

- Introduce ICheckIndexable-adapter for checking if an object is indexable.
  [tom_gross]

- Use proper i18n labels.
  [tom_gross]

- Drop dependency on elementree (in favour of lxml).
  [tom_gross]

- Let getRID return a real integer (like ZCatalog)
  [tom_gross]

- ``solrBase`` should be a string, fixes #8
  [saily]


3.1 - 2013-02-16
----------------

- Add optional plone.app.contentlisting/plone.app.search support
  [do3cc][csenger]

- Add datehandler support for python date objects.
  [jcbrand]

- Add inthandler support for not indexing Integers that are None.
  [do3cc]


3.0 - 2012-02-06
----------------

- Ignore a batch start parameter when selecting a facet to filter on.
  https://github.com/Jarn/collective.solr/issues/12
  [mj]


3.0b5 - 2011-12-07
------------------

- Removed `solr_dump_catalog` and `solr_import_dump` command line scripts.
  They were too dependent on internals and had subtle bugs.
  [hannosch]

- Sort arguments in `buildQuery` to get a stable ordering for test output.
  [hannosch]

- Solr facet queries on unknown fields will now raise a SolrException.
  [hannosch]

- Update example configuration to Solr 3.5.
  [hannosch]

- Fix control panel adapter to save the search_pattern as utf-8.
  [ggozad]


3.0b4 - 2011-11-10
------------------

- Revert `unrestrictedSearchResults` change, as it breaks additional catalogs,
  like the membrane catalogs.
  [hannosch]


3.0b3 - 2011-11-09
------------------

- Made maintenance sync view compatible with latest internals of field indexes.
  [hannosch]

- Also dispatch `unrestrictedSearchResults` to the Solr server.
  https://github.com/Jarn/collective.solr/issues/5
  [reinhardt, hannosch]

- Tweak search form to better match sunburst proportions.
  [elro]


3.0b2 - 2011-10-05
------------------

- Facet titles can now be provided by specialized vocabularies. Register a named
  IFacetTitleVocabularyFactory utility and it'll be used to get a vocabulary
  for the facet field with the same name.
  [mj]


3.0b1 - 2011-09-27
------------------

- Extend the wildcard search term manipulation to do Unicode to ascii folding,
  to keep up with the default field settings of the text field.
  [hannosch, mj]


3.0a5 - 2011-09-26
------------------

- Don't treat search terms ending in numbers as `simple`, as Solr doesn't deal
  with wildcard searches for numbers.
  [hannosch]

- Include CMFCore's `permissions.zcml`.
  [witekdev, hannosch]


3.0a4 - 2011-08-22
------------------

* Fixed bug in `extender.searchwords` indexer - terms need to be lowercased
  explicitly.
  [hannosch]


3.0a3 - 2011-08-22
------------------

* Fixed handling of intra-word hyphens to be taken literally instead of being
  interpreted as syntax for text fields.
  [hannosch]

* Explicitly require Plone 4.1 / Zope 2.13.
  [hannosch]

* Depend on the new c.indexing 2.0a2.
  [hannosch]

* Added an `archetypes.schemaextender` dependency and register two fields for
  all objects providing `IATContentType`. `showinsearch` is a boolean field that
  can be used to hide specific content items from search results. `searchwords`
  is a lines field, which lets you specify words that an object should be found
  under.
  [hannosch]

* Standardize on `solr` as the i18n domain.
  [hannosch]


3.0a2 - 2011-07-10
------------------

* Adjust munin configs for query cache handlers to `c.r.solrinstance 3.5`
  changes using `FastLRUCache`.
  [hannosch]

* Added munin configs for the `/update/extract`, the direct update handler,
  query cache size and warmup time, admin file requests used to get the
  Solr schema and the searcher warmup time.
  [hannosch]

* Added tests for splitting words on `:` and `-`.
  [hannosch]

* Update example configuration to Solr 3.3.
  [hannosch]

* Add `getRID` and `_unrestrictedGetObject` to our flare implementation.
  [hannosch]

* Added documentation on setting up a master-slave configuration using the
  `SolrReplication` support.
  [hannosch]

* Adjust tests to work with latest `collective.recipe.solrinstance = 3.3` and
  its new ICU-based text field.
  [hannosch]


3.0a1 - 2011-06-23
------------------

**Upgrade notes**

* Changed the names of the indexes used to emulate the `path` index. You need
  to adjust your schema and rename `physicalPath` to `path_string`,
  `physicalDepth` to `path_depth` and `parentPaths` to `path_parents`. This
  also requires a full Solr reindex to pick up the new data.
  [hannosch]

**Changes**

* Added `object_provides` index to example schema, as it's used in the
  collection portlet to find collections.
  [hannosch]

* Rewrote the `maintenance/sync` method for more performance, dropped the
  optional `path` restriction from it and removed the `cache` argument. It
  should be able to sync datasets in the 100,000 object range in the matter of
  a couple minutes.
  [hannosch]

* Changed the `maintenance/reindex` method to only flush data to Solr but not
  commit after each batch. Instead we only commit once at the end. You should
  configure auto commit policies on the Solr server side or `commitWithin`.
  [hannosch]

* Adjusted the `mangleQuery` function to calculate extended path indexes from
  the Solr schema instead of hardcoding `path`. If you have any additional
  extended path indexes, you need to provide indexers with the same three
  suffixes as we do ourselves in the `attributes` module for the `path` index
  and add those to the Solr schema.
  [hannosch]

* Added documentation on Java process, monitoring production settings and
  include a number of useful munin plugin configurations.
  [hannosch]

* Updated example config to include production settings and JMX.
  [hannosch]

* Updated example config to collective.recipe.solrinstance 3.1 and Solr 3.2.
  [hannosch]


2.0 - 2011-06-04
----------------

* Updated readme and project description, adding detailed information about how
  Solr works and how we integrate with it.
  [hannosch]


2.0b2 - 2011-05-18
------------------

* Added optional support for the `Lazy` backports founds in catalogqueryplan.
  [hannosch]

* Fixed patch of LazyCat's `__add__` method to patch the base class instead, as
  the method was moved.
  [hannosch]

* Updated test config to Solr 3.1, which should be supported but hasn't seen
  extensive production use.
  [hannosch]

* Avoid using the deprecated `five:implements` directive.
  [hannosch]


2.0b1 - 2011-04-06
------------------

* Rewrite the `isSimpleSearch` function to use a less complex regular
  expression, which doesn't have O(2**n) scaling properties.
  [hannosch]

* Use the standard libraries doctest module.
  [hannosch]

* Fix the pretty_title_or_id method from PloneFlare; the implementation
  was broken, now delegates to the standard Plone implementation.
  [mj]


2.0a3 - 2011-01-26
------------------

* In `solr_dump_catalog` correctly handle boolean values and empty text fields.
  [hannosch]


2.0a2 - 2011-01-10
------------------

* Provide a dummy request in the `solr_dump_catalog` command.
  [hannosch]


2.0a1 - 2011-01-10
------------------

* Handle utf-8 encoded data correctly in `utils.isWildCard`.
  [hannosch]

* Gracefully handle exceptions raised during index data retrieval.
  [tom_gross, hannosch]

* Added `zopectl.command` entry points for three new scripts.
  `solr_clear_index` will remove all entries from Solr. `solr_dump_catalog`
  will efficiently dump the content of the catalog onto the filesystem and
  `solr_import_dump` will import the dump into Solr. This can be used to
  bootstrap an empty Solr index or update it when the boost logic has changed.
  All scripts will either take the first Plone site found in the database or
  accept an unnamed command line argument to specify the id. The Solr server
  needs to be running and the connection info needs to be configured in the
  Plone site. Example use: ``bin/instance solr_dump_catalog Plone``. In this
  example the data would be stored in `var/instance/solr_dump_plone`. The data
  can be transferred between machines and calling `solr_dump_catalog` multiple
  times will append new data to the existing dump. To get Solr up-to-date you
  should still call `@@solr-maintenance/sync`.
  [hannosch, witsch]

* Changed search pattern syntax to use `str.format` syntax and make both
  `{value}` and `{base_value}` available in the pattern.
  [hannosch]

* Add possibility to calculate site-specific boost values via a skin script.
  [hannosch, witsch]

* Fix wildcard searches for patterns other than just ending with an asterisk.
  [hannosch, witsch]

* Require Plone 4.x, declare package dependencies & remove BBB bits.
  [hannosch, witsch]

* Add configurable setting for custom search pattern for simple searches,
  allowing to include multiple fields with specific boost values.
  [hannosch, witsch]

* Don't modify search parameters during indexing.
  [hannosch, witsch]

* Fixed auto-commit support to actually sent the data to Solr, but omit the
  commit message.
  [hannosch]

* Added support for ``commitWithin`` support on add messages as per SOLR-793.
  This feature requires a Solr 1.4 server.
  [hannosch]

* Split out 404 auto-suggestion tests into a separate file and disabled them
  under Plone 4 - the feature is no longer part of Plone.
  [hannosch]

* Fixed error handling code to deal with different exception string
  representations in Python 2.6.
  [hannosch]

* Made tests independent of the ``Large Folder`` content type, as it no longer
  exists in Plone 4.
  [hannosch]

* Avoid using the incompatible TestRequest from zope.publisher inside Zope 2.
  [hannosch]

* Fixed undefined variables in ``search.pt`` for Plone 4 compatibility.
  [hannosch]


1.1 - Released March 17, 2011
-----------------------------

* Still index, if a field can't be accessed.
  [tom_gross]

* Fix the pretty_title_or_id method from PloneFlare; the implementation
  was broken, now delegates to the standard Plone implementation.
  [mj]


1.0 - Released September 14, 2010
---------------------------------

* Enable multi-field "fq" statements.
  [tesdal, witsch]

* Prevent logging of "unknown" search attributes for `use_solr` and the
  infamous `-C` Zope startup parameter.
  [witsch]


1.0rc3 - Released September 9, 2010
-----------------------------------

* Add logging of queries without explicit "rows" parameter.
  [witsch]

* Add configuration to exclude user from ``allowedRolesAndUsers`` for
  better cacheability.
  [tesdal, witsch]

* Add configuration for effective date steps.
  [tesdal, witsch]

* Handle python `datetime` and `date` objects.
  [do3cc, witsch]

* Fixed a grammar error in ``error.pt``.
  [hannosch]


1.0rc2 - Released August 31, 2010
---------------------------------

* Fix regression about catalog fallback with required, but empty parameters.
  [tesdal, witsch]


1.0rc1 - Released July 30, 2010
-------------------------------

* Handle broken or timed out connections during schema retrieval gracefully.
  Refs http://plone.org/products/collective.solr/issues/23
  [ftoth, witsch]


1.0b24 - Released July 29, 2010
-------------------------------

* Fix security issue with `getObject` on Solr flares, which used unrestricted
  traversal on the entire path, potentially leading to information leaks.
  Refs http://plone.org/products/collective.solr/issues/27
  [pilz, witsch]

* Add missing `CreationDate` method to flares.
  This fixes http://plone.org/products/collective.solr/issues/16
  [witsch]

* Add logging for slow queries along with the query time as reported by Solr.
  [witsch]

* Limit number of matches looked up during live search for speedier replies.
  [witsch]

* Renamed the batch parameters to ``b_start`` and ``b_size`` to avoid
  conflicts with index names and be consistent with existing template code.
  [do3cc]

* Added a new config option ``auto-commit`` which is enabled by default. You
  can disable this, which avoids any explicit commit messages to be sent to
  the Solr server by the client. You have to configure commit policies on
  the server side instead.
  [hannosch]

* Added support for a special query key ``use_solr`` which forces queries to
  be sent to Solr even though none of the required keys match. This can be
  used to sent individual catalog queries to Solr.
  [hannosch]


1.0b23 - Released May 15, 2010
------------------------------

* Add support for batching, i.e. only fetch and parse items from Solr,
  which are part of the currently handled batch.
  [witsch]

* Fix quoting of operators for multi-word search terms.
  [witsch]

* Use the faster C implementations of `elementtree`/`xml.etree` if available.
  [hannosch, witsch]

* Grant restricted code access to the search results, e.g. skin scripts.
  [do3cc, witsch]

* Fix handling of 'depth' argument when querying multiple paths.
  [reinhardt, witsch]

* Don't break when filter queries should be used for all parameters.
  [reinhardt, witsch]

* Always provide values for all metadata columns like the catalog does.
  [witsch]

* Always fall back to portal catalog for "navtree" queries so the set of
  required query parameters can be empty.
  This refs http://plone.org/products/collective.solr/issues/18
  [reinhardt, witsch]

* Prevent parsing errors for dates from before 1000 A.D. in combination
  with 32-bit systems and Solr 1.4.
  [reinhardt, witsch]

* Don't process content with its own indexing methods, e.g. ``reindexObject``,
  via the `reindex` maintenance view.
  [witsch]

* Let query builder handle sets of possible boolean values as passed by
  boolean topic criteria for example.
  [hannosch, witsch]

* Recognize new ``solr.TrieDateField`` field type and handle it in the same
  way as we handle the older ``solr.DateField``.
  [hannosch]

* Warn about missing search indices and non-stored sort parameters.
  [witsch]

* Fix issue when reindexing objects with empty date fields.
  [witsch]

* Changed the default schema for ``is_folderish`` to store the value. The
  reference browser search expects it on the brain.
  [hannosch]

* Changed the GenericSetup export/import handler for the Solr manager to
  ignore non-persistent utilities.
  [hannosch]

* Add support for `LinguaPlone`.
  [witsch]

* Update sample Solr buildout configuration and documentation to recommend a
  high enough default setting for maximum search results returned by Solr.
  This refs http://plone.org/products/collective.solr/issues/20
  [witsch]


1.0b22 - Released February 23, 2010
-----------------------------------

* Split out a ``BaseSolrConnectionConfig`` class, to be used for registering a
  non-persistent connection configuration.
  [hannosch]

* Fix bug regarding timeout locking.
  [witsch]

* Convert test setup to `collective.testcaselayer`.
  [witsch]

* Only apply timeout decorator when actually committing changes to Solr,
  also re-enabling the use of query parameters for maintenance views again.
  [witsch]

* We also need to change the ``SearchDispatcher`` to use the original method
  in case Solr isn't active.
  [hannosch]

* Changed the ``searchResults`` monkey to store and use the method found on
  the class instead of assuming it comes from the base class.  This makes
  things work with `LinguaPlone` which also patches this method.
  [hannosch]

* Add dutch translation.
  [WouterVH]

* Refactor buildout to allow running tests against Plone 4.x.
  [witsch]

* Optimize reindex behavior when populating the Solr index for the first time.
  [hannosch, witsch]

* Only register indexable attributes the old way on Plone 3.x.
  [jcbrand]

* Fix timeout decorator to work ttw.
  [hannosch, witsch]

* Add "z3c.autoinclude.plugin" entry point, so in Plone 3.3+ you can avoid
  loading the ZCML file.
  [hannosch]


1.0b21 - Released February 11, 2010
-----------------------------------

* Fix unindexing to not fetch more data from the objects than necessary.
  [witsch]

* Use decorator to lock timeouts and make sure the lock is always released.
  [witsch]

* Fix maintenance views to work without setting up a Solr connection first.
  [witsch]


1.0b20 - Released January 26, 2010
----------------------------------

* Fix reindexing to always provide data for all fields defined in the schema
  as support for "updateable/modifiable documents" is only planned for Solr
  1.5.  See https://issues.apache.org/jira/browse/SOLR-139 for more info.
  [witsch]

* Fix CSS issues regarding facet display on IE6.
  [witsch]


1.0b19 - Released January 24, 2010
----------------------------------

* Fix partial reindexing to preserve data for indices that are not stored.
  [witsch]

* Help with improved logging of auto-flushes for easier performance tuning.
  [witsch]


1.0b18 - Released January 23, 2010
----------------------------------

* Work around layout issue regarding facet counts on IE6.
  [witsch]


1.0b17 - Released January 21, 2010
----------------------------------

* Don't confuse pre-configured filter queries with facet selections.
  [witsch]

* Always display selected facets, even, or especially, without search results.
  [witsch]


1.0b16 - Released January 11, 2010
----------------------------------

* Remove `catalogSync` maintenance view since it would need to fetch
  additional data (for non-stored indices) from the objects themselves in
  order to work correctly.
  [witsch]

* Fix `reindex` maintenance view to preserve data that cannot be fetched from
  Solr during partial indexing, i.e. indices that are not stored.
  [witsch]

* Use wildcard searches for simple search terms to reflect Plone's default
  behaviour.
  [witsch]

* Fix drill-down for facet values containing white space.
  [witsch]

* Add support for partial syncing of catalog and solr indexes.
  [witsch]


1.0b15 - Released October 12, 2009
----------------------------------

* Filter control characters from all input to prevent indexing errors.
  This refs http://plone.org/products/collective.solr/issues/1
  [witsch]


1.0b14 - Released September 17, 2009
------------------------------------

* Fix query builder to use explicit `OR`\s so that it becomes possible to
  change Solr's default operator to `AND`.
  [witsch]

* Remove relevance information from search results as they don't make sense
  to the user.
  [witsch]


1.0b13 - Released August 20, 2009
---------------------------------

* Fix `reindex` and `catalogSync` maintenance views to not pass invalid data
  back to Solr when indexing an explicit list of attributes.
  [witsch]


1.0b12 - Released August 15, 2009
---------------------------------

* Fix `reindex` maintenance view to keep any existing data when indexing a
  given list of attributes.
  [witsch]

* Add support for facet dependencies: Specifying a facet "foo" like "foo:bar"
  only makes it show up when a value for "bar" has been previously selected.
  [witsch]

* Allow indexer methods to raise `AttributeError` to prevent an attribute
  from being indexed.
  [witsch]


1.0b11 - Released July 2, 2009
------------------------------

* Fix maintenance view for adding/syncing single indexes using catalog data.
  [witsch]

* Allow to configure query parameters for which filter queries should be
  used (see http://wiki.apache.org/solr/FilterQueryGuidance for more info)
  [fschulze, witsch]

* Encode unicode strings when building facet links.
  [fschulze, witsch]

* Fix facet display to try to keep the given order of facets.
  [witsch]

* Allow facet values to be translated.
  [witsch]


1.0b10 - Released June 11, 2009
-------------------------------

* Range queries must not be quoted with the new query parser.
  [witsch]

* Disable socket timeouts during maintenance tasks.
  [witsch]

* Close the response object after searching in order to avoid
  `ResponseNotReady` errors triggering duplicate queries.
  [witsch]

* Use proper way of accessing jQuery & fix IE6 syntax error.
  [fschulze]

* Format relevance value for search results.
  [witsch]


1.0b9 - Released May 12, 2009
-----------------------------

* Add safety net for using a translation map on unicode strings.
  This fixes http://plone.org/products/collective.solr/issues/4
  [witsch]

* Add workaround for issue with `SearchableText` criteria in topics.
  This fixes http://plone.org/products/collective.solr/issues/3
  [witsch]

* Add maintenance view for adding/syncing single indexes using already
  existing data from the portal catalog.
  [witsch]

* Fix hard-coded unique key in maintenance view.
  [witsch]


1.0b8 - Released May 4, 2009
----------------------------

* Fix indexing regarding Plone 3.3, `plone.indexer`_ & `PLIP 239`_.
  This fixes http://plone.org/products/collective.solr/issues/6
  [witsch]

  .. _`plone.indexer`: http://pypi.python.org/pypi/plone.indexer/
  .. _`PLIP 239`: http://plone.org/products/plone/roadmap/239


1.0b7 - Released April 28, 2009
-------------------------------

* Fix unintended (de)activation of the Solr integration during profile
  (re)application.
  [witsch]

* Fix display of facet information with no active facets.
  [witsch]

* Register import and export steps using ZCML.
  [witsch]


1.0b6 - Released April 20, 2009
-------------------------------

* Add support for facetted searches.
  [witsch]

* Update code to comply to PEP8 style guide lines.
  [witsch]

* Expose additional information provided by Solr - for example about headers
  and search facets.
  [witsch]

* Handle edge cases like invalid range queries by quoting
  [tesdal]

* Parse and quote the query to filter invalid query syntax.
  [tesdal]

* In solrSearchResults, if the passed in request is a dict, look up
  request to enable adaptation into PloneFlare.
  [tesdal]

* Added support for objects with a 'query' attribute as search values.
  [tmog]


1.0b5 - Released December 16, 2008
----------------------------------

* Fix and extend logging in "sync" maintenance view.
  [witsch]


1.0b4 - Released November 23, 2008
----------------------------------

* Filter control characters to prevent indexing errors.  This fixes
  http://plone.org/products/collective.solr/issues/1
  [witsch]

* Avoid using brains when getting all objects from the catalog for sync runs.
  [witsch]

* Prefix output from maintenance views with a time-stamp.
  [witsch]


1.0b3 - Released November 12, 2008
----------------------------------

* Fix url fallback during schema retrieval.
  [witsch]

* Fix issue regarding quoting of white space when searching.
  [witsch]

* Make indexing operations more robust in case the schema is missing a
  unique key or couldn't be parsed.
  [witsch]


1.0b2 - Released November 7, 2008
---------------------------------

* Make schema retrieval slightly more robust to not let network failures
  prevent access to the site.
  [witsch]


1.0b1 - Released November 5, 2008
---------------------------------

* Initial release
  [witsch]
