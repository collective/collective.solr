Spelling checking / suggestions
*******************************

Solr supports spell checking - or rather suggestions,
as it doesn't contain a formal dictionary but bases suggestions on the indexed corpus.
The idea is to present the user with alternative search terms for any query that is likely to produce more or better results.

Currently this is not yet exposed in the `collective.solr` API's.
Solr server, as set up by the buildout recipe, already contains the required configuration for this.
