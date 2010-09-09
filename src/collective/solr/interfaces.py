from zope.interface import Interface
from zope.schema import Bool, TextLine, Int, Float, List, Choice
from zope.i18nmessageid import MessageFactory
from collective.indexing.interfaces import IIndexQueueProcessor

_ = MessageFactory('collective.solr')


class ISolrSchema(Interface):

    active = Bool(title=_(u'Active'), default=False,
        description=_(u'Check this to enable the Solr integration, i.e. '
                       'indexing and searching using the below settings.'))

    host = TextLine(title=_(u'Host'),
        description=_(u'The host name of the Solr instance to be used.'))

    port = Int(title=_(u'Port'),
        description=_(u'The port of the Solr instance to be used.'))

    base = TextLine(title=_(u'Base'),
        description=_(u'The base prefix of the Solr instance to be used.'))

    async = Bool(title=_(u'Asynchronous indexing'), default=False,
        description=_(u'Check to enable asynchronous indexing operations, '
                       'which will improve Zope response times in return for '
                       'not having the Solr index updated immediately.'))

    auto_commit = Bool(title=_(u'Automatic commit'), default=True,
        description=_(u'If enabled each index operation will cause a commit '
                       'to be sent to Solr, which causes it to update its '
                       'index. If you disable this, you need to configure '
                       'commit policies on the Solr server side.'))

    index_timeout = Float(title=_(u'Index timeout'),
        description=_(u'Number of seconds after which an index request will '
                       'time out. Set to "0" to disable timeouts.'))

    search_timeout = Float(title=_(u'Search timeout'),
        description=_(u'Number of seconds after which a search request will '
                       'time out. Set to "0" to disable timeouts.'))

    max_results = Int(title=_(u'Maximum search results'),
        description=_(u'Specify the maximum number of matches to be returned '
                       'when searching. Set to "0" to always return all '
                       'results.'))

    required = List(title=_(u'Required query parameters'),
        description = _(u'Specify required query parameters, one per line. '
                         'Searches will only get dispatched to Solr if any '
                         'of the listed parameters is present in the query. '
                         'Leave empty to dispatch all searches.'),
        value_type = TextLine(), default = [], required = False)

    facets = List(title=_(u'Default search facets'),
        description = _(u'Specify catalog indexes that should be queried for '
                         'facet information, one per line.'),
        value_type = TextLine(), default = [], required = False)

    filter_queries = List(title=_(u'Filter query parameters'),
        description = _(u'Specify query parameters for which filter queries '
                         'should be used, one per line.  Please note that '
                         'the below list of indexes might not be complete '
                         'if the Solr server is not running or the '
                         'connection hasn\'t been activated yet.'),
        value_type = Choice(vocabulary='collective.solr.indexes'),
        default = [], required = False)

    slow_query_threshold = Int(title=_(u'Slow query threshold'),
        description=_(u'Specify a threshold (in milliseconds) after which '
                       'queries are considered to be slow causing them to '
                       'be logged. Set to "0" to prevent any logging.'))

    effective_steps = Int(title=_(u'Effective date steps'), default=1,
        description=_(u'Specify the effective date steps in seconds. '
                       'Using 900 seconds (15 minutes) means the effective '
                       'date sent to Solr changes every 15 minutes.'))


class ISolrConnectionConfig(ISolrSchema):
    """ utility to hold the connection configuration for the solr server """


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

    def buildQuery(default=None, **args):
        """ helper to build a query for simple use-cases; the query is
            returned as a dictionary which might be string-joined or
            passed to the `search` method as the `query` argument """


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

    def reindex(batch=100, skip=0, cache=1000):
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """

    def sync(batch=100, cache=1000):
        """ sync the solr index with the portal catalog;  records contained
            in the catalog but not in solr will be indexed and records not
            contained in the catalog can be optionally removed;  this can
            be used to ensure consistency between zope and solr after the
            solr server has been unavailable etc """
