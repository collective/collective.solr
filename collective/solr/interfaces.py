from zope.interface import Interface
from collective.indexing.interfaces import IIndexQueueProcessor


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

    def clear(self):
        """ clear all data from solr, i.e. delete all indexed objects """

    def reindex():
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """

