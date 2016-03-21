Exclude from search and elevation
---------------------------------

By default this add-on introduces two new fields to the default content types or any custom type derived from ATContentTypes.

The `showinsearch` boolean field lets you hide specific content items from the search results,
by setting the value to `false`.

The `searchwords` lines field allows you to specify multiple phrases per content item.
A phrase is specified per line.
User searches containing any of these phrases will show the content item as the first result for the search. 
This technique is also known as `elevation`.

Both of these features depend on the default `search-pattern` to include the required parts as included in the default configuration. 
The `searchwords` approach to elevation doesn't depend on the Solr elevation feature,
as that would require maintaining a xml file as part of the Solr server configuration.
