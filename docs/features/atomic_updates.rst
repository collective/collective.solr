Partial indexing documents (AtomicUpdates)
******************************************

This means whenever possible,
only the necessary/specified attributes get updated in Solr,
and more importantly,
re-indexed by Plone's indexers.

With collective.recipe.solr a new configuration is introduced,
called ``updateLog``.
``updateLog`` is enabled by default and allows atomic updates.
In detail it adds a new field ``_version_`` to the schema and also adds "<updateLog />" to your solr config.

Further all your indexes configured in solr.cfg needs the ``stored:true`` attribute (except the ``default`` field).

See http://wiki.apache.org/solr/Atomic_Updates for details.

Also note, that the AtomicUpdate feature is no compatible with the "Index time boost" feature.
You have to decide, whether using atomic updates, or boosting on index time.
You can enable/disable atomic updates through the collective.solr control panel.
Atomic updates are enabled by default.
