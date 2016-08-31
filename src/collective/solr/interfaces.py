# -*- coding: utf-8 -*-
from collective.indexing.interfaces import IIndexQueueProcessor
from zope.interface import Interface
from zope.schema import Bool
from zope.schema import Float
from zope.schema import Int
from zope.schema import List
from zope.schema import Text
from zope.schema import TextLine
from zope.schema.interfaces import IVocabularyFactory

from collective.solr import SolrMessageFactory as _


class ISolrSchema(Interface):

    active = Bool(
        title=_('label_active', default=u'Active'),
        description=_(
            'help_active',
            default=u'Check this to enable the Solr integration, i.e. '
                    u'indexing and searching using the below settings.'
        ),
        default=False,
    )

    host = TextLine(
        title=_('label_host', default=u'Host'),
        description=_(
            'help_host',
            default=u'The host name of the Solr instance to be used.'
        )
    )

    port = Int(
        title=_('label_port', default=u'Port'),
        description=_(
            'help_port',
            default=u'The port of the Solr instance to be used.'
        )
    )

    base = TextLine(
        title=_('label_base', default=u'Base'),
        description=_(
            'help_base',
            default=u'The base prefix of the Solr instance to be used.'
        )
    )

    async = Bool(
        title=_('label_async', default=u'Asynchronous indexing'),
        default=False,
        description=_(
            'help_async',
            default=u'Check to enable asynchronous indexing operations, '
                    u'which will improve Zope response times in return for '
                    u'not having the Solr index updated immediately.'
        )
    )

    auto_commit = Bool(
        title=_('label_auto_commit', default=u'Automatic commit'),
        default=True,
        description=_(
            'help_auto_commit',
            default=u'If enabled each index operation will cause a commit '
                    u'to be sent to Solr, which causes it to update its '
                    u'index. If you disable this, you need to configure '
                    u'commit policies on the Solr server side.'
        )
    )

    commit_within = Int(
        title=_('label_commit_within', default=u'Commit within'),
        default=0,
        description=_(
            'help_commit_within',
            default=u'Maximum number of milliseconds after which adds '
                    u'should be processed by Solr. Defaults to 0, meaning '
                    u'immediate commits. Enabling this feature implicitly '
                    u'disables automatic commit and you should configure '
                    u'commit policies on the Solr server side. Otherwise '
                    u'large numbers of deletes without adds will not be '
                    u'processed. This feature requires a Solr 1.4 server.'
        )
    )

    index_timeout = Float(
        title=_('label_index_timeout',
                default=u'Index timeout'),
        description=_(
            'help_index_timeout',
            default=u'Number of seconds after which an index request will '
                    u'time out. Set to "0" to disable timeouts.'
        )
    )

    search_timeout = Float(
        title=_('label_search_timeout',
                default=u'Search timeout'),
        description=_(
            'help_search_timeout',
            default=u'Number of seconds after which a search request will '
                    u'time out. Set to "0" to disable timeouts.'
        )
    )

    max_results = Int(
        title=_('label_max_results',
                default=u'Maximum search results'),
        description=_(
            'help_max_results',
            default=u'Specify the maximum number of matches to be returned '
                    u'when searching. Set to "10000000" or some other '
                    u'ridiculously large value that is higher than the '
                    u'possible number of rows that are expected.'
        ),
        default=1000000,
    )

    required = List(
        title=_('label_required', default=u'Required query parameters'),
        description=_(
            'help_required',
            default=u'Specify required query parameters, one per line. '
                    u'Searches will only get dispatched to Solr if any '
                    u'of the listed parameters is present in the query. '
                    u'Leave empty to dispatch all searches.'
        ),
        value_type=TextLine(),
        default=[],
        missing_value=[],
        required=False
    )

    search_pattern = Text(
        title=_('label_search_pattern',
                default=u'Pattern for simple search queries'),
        description=_(
            'help_search_pattern',
            default=u'Specify a query pattern used for simple queries '
                    u'consisting only of words and numbers, i.e. not '
                    u'using any of Solr\'s advanced query expressions. '
                    u'{value} and {base_value} are available in the '
                    u'pattern and will be replaced by the search word '
                    u'and the search word stripped of wildcard symbols.'
        )
    )

    facets = List(
        title=_('label_facets', default=u'Default search facets'),
        description=_(
            'help_facets',
            default=u'Specify catalog indexes that should be queried for '
                    u'facet information, one per line.'),
        value_type=TextLine(),
        default=[],
        required=False
    )

    filter_queries = List(
        title=_('label_filter_queries', default=u'Filter query parameters'),
        description=_(
            'help_filter_queries',
            default=u'Specify query parameters for which filter queries '
                    u'should be used, one per line.  You can use several '
                    u'indices in one filter query separated by space. '
                    u'Typical examples are '
                    u'"effective expires allowedRolesAndUsers" or '
                    u'"review_state portal_type".'
        ),
        value_type=TextLine(),
        default=[],
        required=False
    )

    slow_query_threshold = Int(
        title=_('label_slow_query_threshold',
                default=u'Slow query threshold'),
        description=_(
            'help_slow_query_threshold',
            default=u'Specify a threshold (in milliseconds) after which '
                    u'queries are considered to be slow causing them to '
                    u'be logged. Set to "0" to prevent any logging.'
        ),
        default=0,
    )

    effective_steps = Int(
        title=_('label_effective_steps',
                default=u'Effective date steps'),
        default=1,
        description=_(
            'help_effective_steps',
            default=u'Specify the effective date steps in seconds. '
                    u'Using 900 seconds (15 minutes) means the effective '
                    u'date sent to Solr changes every 15 minutes.'))

    exclude_user = Bool(
        title=_('label_exclude_user',
                default=u'Exclude user from allowedRolesAndUsers'),
        description=_(
            'help_exclude_user',
            default=u'Specify whether the user:userid should be excluded '
                    u'from allowedRolesAndUsers to improve cacheability '
                    u'on the expense of finding content with local roles'
                    u'given to specific users.'),
        default=False
    )

    highlight_fields = List(
        title=_(u'Highlighting fields'),
        description=_(
            u'Fields that should be used for highlighting. '
            u'Snippets of text will be generated from the contents '
            u' of these fields, with the search keywords that'
            u'matched highlighted inside the text.'
        ),
        value_type=TextLine(),
        default=[],
        required=False
    )

    highlight_formatter_pre = TextLine(
        title=_(u'Highlight formatter: pre'),
        description=_(u'The text to insert before the highlighted keyword.'),
        default=u'[', required=False
    )

    highlight_formatter_post = TextLine(
        title=_(u'Highlight formatter: post'),
        description=_(u'The text to insert after the highlighted keyword.'),
        default=u']',
        required=False
    )

    highlight_fragsize = Int(
        title=_(u'Highlight Fragment Size'), default=100,
        description=_(
            u'The size, in characters, of the snippets (aka '
            U'fragments) created by the highlighter.'
        )
    )

    field_list = List(
        title=_(u'Default fields to be returned'),
        description=_(u'Specify metadata fields that should be returned for '
                      u'items in the result set, one per line. Defaults to '
                      u'all available plus ranking score.'),
        value_type=TextLine(),
        default=[],
        required=False
    )

    levenshtein_distance = Float(
        title=_('label_levenshtein_distance',
                default=u'Levenshtein distance'),
        description=_(
            'help_levenshtein_distance',
            default=u'The Levenshtein distance is a string metric for '
                    u'measuring the difference between two strings. It allows'
                    u'you to perform fuzzy searches by specifying a value '
                    u'between 0 and 1.'
        ),
        required=False,
        default=0.0,
    )

    atomic_updates = Bool(
        title=_('label_atomic_updates',
                default=u'Enable atomic updates'),
        description=_(
            'help_atomic_updates',
            default=u'Atomic updates allows you to update only specific '
                    u'indexes, like "reindexObject(idxs=["portal_type"])".'
                    u'Unfortunately atomic updates are not compatible with '
                    u'index time boosting. If you enable atomic updates, '
                    u'index time boosting no longer works.'),
        default=True,
        required=False,
    )

    boost_script = Text(
        title=_('label_boost_script',
                default=u'Python script for custom index boosting'),
        required=False,
        default=u'',
        missing_value=u'',
        description=_(
            'help_search_pattern',
            default=u'This script is meant to be customized according to '
                    u'site-specific search requirements, e.g. boosting '
                    u'certain content types like "news items", ranking older '
                    u'content lower, consider special important content items,'
                    u' content rating etc.'
                    u' the indexing data that will be sent to Solr is passed '
                    u'in as the `data` parameter, the indexable object is '
                    u'available via the `context` binding. The return value '
                    u'should be a dictionary consisting of field names and '
                    u'their respecitive boost values.  use an empty string '
                    u'as the key to set a boost value for the entire '
                    u'document/content item.'
        )
    )


class ISolrConnectionConfig(ISolrSchema):
    """ utility to hold the connection configuration for the solr server """


class IZCMLSolrConnectionConfig(Interface):
    """Solr connection settings configured through ZCML.
    """


class ISolrConnectionManager(Interface):
    """ a thread-local connection manager for solr """

    def setHost(active=False, host='localhost', port=8983, base='/solr'):
        """ set connection parameters """

    def closeConnection(clearSchema=False):
        """ close the current connection, if any """

    def getConnection():
        """ returns an existing connection or opens one """

    def getSchema():
        """ returns the currently used schema or fetches it.
            If the schema cannot be fetched None is returned. """

    def setTimeout(timeout, lock=object()):
        """ set the timeout on the current (or to be opened) connection
            to the given value and optionally lock it until explicitly
            freed again """

    def setIndexTimeout():
        """ set the timeout on the current (or to be opened) connection
            to the value specified for indexing operations """

    def setSearchTimeout():
        """ set the timeout on the current (or to be opened) connection
            to the value specified for search operations """


class ISolrIndexQueueProcessor(IIndexQueueProcessor):
    """ an index queue processor for solr """


class ISolrFlare(Interface):
    """ a sol(a)r brain, i.e. a data container for search results """


class IFlare(Interface):
    """ marker interface for pluggable brain wrapper classes, providing
        additional helper methods like `getURL` etc """


class ISearch(Interface):
    """ a generic search interface
        FIXME: this should be defined in a generic package """

    def search(query, **parameters):
        """ perform a search with the given querystring and extra parameters
            (see http://wiki.apache.org/solr/CommonQueryParameters) """

    def __call__(query, **parameters):
        """ convenience alias for `search` """

    def buildQueryAndParameters(default=None, **args):
        """ helper to build a query for simple use-cases; the query is
            returned as a dictionary which might be string-joined or
            passed to the `search` method as the `query` argument,
            additionally search parameters are substracted from the
            args and returned as a separate dict"""


class ICatalogTool(Interface):
    """ marker interface for plone's catalog tool """


class ISearchDispatcher(Interface):
    """ adapter for potentially dispatching a given query to an
        alternative search backend (instead of the portal catalog) """

    def __call__(request, **keywords):
        """ decide if an alternative search backend is capable of performing
            the given query and use it or fall back to the portal catalog """


class ISolrMaintenanceView(Interface):
    """ solr maintenance view for clearing, re-indexing content etc """

    def optimize():
        """ optimize solr indexes """

    def clear():
        """ clear all data from solr, i.e. delete all indexed objects """

    def reindex(batch=1000, skip=0):
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """

    def sync(batch=1000):
        """ sync the solr index with the portal catalog;  records contained
            in the catalog but not in solr will be indexed and records not
            contained in the catalog can be optionally removed;  this can
            be used to ensure consistency between zope and solr after the
            solr server has been unavailable etc """

    def cleanup(batch=1000):
        """ remove entries from solr that don't have a corresponding Zope
            object  or have a different UID than the real object"""


class ISolrAddHandler(Interface):
    """ An adder for solr documents """


class IFacetTitleVocabularyFactory(IVocabularyFactory):
    """A vocabulary factory used to create a vocabulary that provides titles
    for facet values

    When facet values are displayed for selection on the search results page, a
    named IFacetTitleVocabularyFactory is looked up, and if it exists it's
    called to return a zope.schema.IBaseVocabulary vocabulary. The name is the
    same as the facet name (e.g. "portal_type" or "review_state"). This
    vocabulary should return zope.schema.ITitledTokenizedTerm items, their
    title attribute is what is displayed in the UI.
    """


class ICheckIndexable(Interface):
    """ Check if an object is indexable """

    def __call__():
        """ Return `True`, if context is indexable and `False`otherwise
        """
