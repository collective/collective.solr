## Script (Python) "solr_boost_index_values"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=data
##title=Calculate field and document boost values for Solr

# this script is meant to be customized according to site-specific
# search requirements, e.g. boosting certain content types like "news items",
# ranking older content lower, consider special important content items,
# content rating etc.
#
# the indexing data that will be sent to Solr is passed in as the `data`
# parameter, the indexable object is available via the `context` binding.
# the return value should be a dictionary consisting of field names and
# their respecitive boost values.  use an empty string as the key to set
# a boost value for the entire document/content item.

return {}
