Dependencies
------------

Currently we depend on `collective.indexing` as a means to hook into the normal catalog machinery of Plone to detect content changes.
`c.indexing` before version two had some persistent data structures that frequently caused problems when removing the add-on.
These problems have been fixed in version two.
Unfortunately `c.indexing` still has to hook the catalog machinery in various evil ways,
as the machinery lacks the required hooks for its use-case.
Going forward it is expected for `c.indexing` to be merged into the underlying `ZCatalog` implementation,
at which point `collective.solr` can use those hooks directly.
