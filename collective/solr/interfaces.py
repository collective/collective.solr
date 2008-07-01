from zope.interface import Interface
from zope.schema import Bool, TextLine, Int
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
        """ returns the currently used schema or fetches it """


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
        """ helper to build a querystring for simple use-cases """


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

