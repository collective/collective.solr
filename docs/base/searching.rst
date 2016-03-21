Searching
*********

Information retrieval is a complex science.
We try to give a very brief explanation here,
refer to the literature and documentation of Lucene/Solr for much more detailed information.

If you do searches in normal Plone,
you have a search term and query the SearchableText index with it.
The SearchableText is a simple concatenation of all searchable fields,
by default title, description and the body text.

The default ZCTextIndex in Plone uses a simplified version of the Okapi BM25 algorithm described in papers in 1998.
It uses two metrics to score documents:

- Term frequency: How often does a search term occur in a document
- Inverse document frequency: The inverse of in how many documents a term occurs.
  Terms only occurring in a few documents are scored higher than those occurring in many documents.

It calculates the sum of all scores, for every term common to the query and any document.
So for a query with two terms,
a document is likely to score higher if it contains both terms,
except if one of them is a very common term and the other document contains the non-common term more often.

The similarity function used in Solr/Lucene uses a different algorithm,
based on a combination of a boolean and vector space model,
but taking the same underlying metrics into account.
In addition to the term frequency and inverse document frequency Solr respects some more metrics:

- length normalization: The number of all terms in a field.
  Shorter fields contribute higher scores compared to long fields.
- boost values: There's a variety of boost values that can be applied, both index-time document boost values as well as boost values per search field or search term

In its pre 2.0 versions,
collective.solr used a naive approach and mirrored the approach taken by ZCTextIndex.
So it sent each search query as one query and matched it against the full SearchableText field inside Solr.
By doing that Solr basically used the same algorithm as ZCTextIndex as it only had one field to match with the entire text in it.
The only difference was the use of the length normalization,
so shorter documents ranked higher than those with longer texts.
This actually caused search quality to be worse,
as you'd frequently find folders, links or otherwise rather empty documents.
The Okapi BM25 implementation in ZCTextIndex deliberately ignores the document length for that reason.

In order to get good or better search quality from Solr,
we have to query it in a different way.
Instead of concatenating all fields into one big text,
we need to preserve the individual fields and use their intrinsic importance.
We get the main benefit be realizing that matches on the title and description are more important than matches on the body text or other fields in a document.
collective.solr 2.0+ does exactly that by introducing a `search-pattern` to be used for text searches.
In its default form it causes each query to work against the title,
description and full searchable text fields and boosts the title by a high and the description by a medium value.
The length normalization already provides an improvement for these fields,
as the title is likely short,
the description a bit longer and the full text even longer.
By using explicit boost values the effect gets to be more pronounced.

If you do custom searches or want to include more fields into the full text search you need to keep the above in mind.
Simply setting the `searchable` attribute on the schema of a field to `True` will only include it in the big searchable text stream.
If you for example include a field containing tags,
the simple tag names will likely 'drown' in the full body text.
You might want to instead change the search pattern to include the field and potentially put a boost value on it - though it will be more important as it's likely to be extremely short.
Similarly extracting the full text of binary files and simply appending them into the search stream might not be the best approach.
You should rather index those in a separate field and then maybe use a boost value of less than one to make the field less important.
Given two documents with the same content,
one as a normal page and one as a binary file,
you'll likely want to find the page first,
as it's faster to access and read than the file.

There's a good number of other improvements you can do using query time and index time boost values.
To provide index time boost values,
you can provide a skin script called `solr_boost_index_values` which gets the object to be indexed and the data sent to Solr as arguments and returns a dictionary of field names to boost values for each document.
The safest is to return a boost value for the empty string,
which results in a document boost value.
Field level boost values don't work with all searches,
especially wildcard searches as done by most simple web searches.
The index time boost allows you to implement policies like boosting certain content types over others,
taking into account ratings or number of comments as a measure of user feedback or anything else that can be derived from each content item.
