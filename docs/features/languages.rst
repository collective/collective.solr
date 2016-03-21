Supported scripts and languages
*******************************

In the default configuration all languages and scripts should be supported.
This broad support comes at the expense of avoiding any language specific configuration.

The default text analysis uses libraries based on ICU standards to fold and normalize any text as well as find token boundaries - in most languages word boundaries.

Accented characters are folder into their unaccented base form and many other characters are normalized.
This normalization is similar to what Plone does when generating url identifiers from titles.
These changes are applied both to the indexed text and the user provided search query,
so in general there's a large number of matches at the expense of specificity.

Non-alphabetic characters like hyphens, dots and colons are interpreted as word boundaries,
while case changes and alphanumeric combinations are left intact;
for example `WiFi` or `IPv4` will only be lower-cased but not split.

For any specific site, you likely know the supported content languages and could further tune the text analysis.
A common example is the use of stemming, to generate base words for terms.
This helps to avoid distinctions between singular and plural forms of a word or it being used as an adjective.
Stemming broadens the found result even more, at a greater expense of specificity and needs to be used carefully.

There's a plethora of text analysis options available in Solr if you are interested in the subject or have specific needs.
