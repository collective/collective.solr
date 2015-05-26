Search Term Highlighting
************************

Solr can return snippets of text in which the search term occurs.
The size of the snippets is configurable as are the strings that the search terms will be wrapped in.

For highlighting to work the target field must be a "stored" field in the Solr schema.
Usually you'll want to use SearchableText for highlighting.
However, the contents of the SearchableText field tend to be quite large.
Without further configuration the full contents of the SearchableText of all result items will be transferred from Solr to Plone.
To avoid this you can define a list of fields to be returned from Solr.
Omitting SearchableText from this list might solve network or memory problems that could otherwise occur.
