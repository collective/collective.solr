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


class ISearch(Interface):
    """ a generic search interface
        FIXME: this should be defined in a generic package """

    def search(**query):
        """ perform a search with the given parameters """

    def __call__(**query):
        """ convenience alias for `search` """


