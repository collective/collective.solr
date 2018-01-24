Wildcard searches
*****************

Wildcard search support in Solr is rather poor.
Unfortunately Plone's live search uses this by default, so we have to support it.
When doing wildcard searches,
Solr ignores any of the tokenizer and analyzer settings of the field at query time.

This often leads to a mismatch of the indexed data as modified by those settings and the query term.
In order to work around this, we try to reproduce the essential parts of these analyzers on the `collective.solr` side.
The most common changes are lower-casing characters and folding non-ascii characters to ascii as done by the `ICUFoldingFilterFactory`.

Currently these two changes are hard-wired and applied to all fields of type `solr.TextField`.
If you have different field settings you might need to overwrite `collective.solr.utils.prepare_wildcard`.
