from logging import getLogger
from persistent import Persistent
from zope.interface import implements
from zope.component import getUtility
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.solr import SolrConnection
from collective.solr.local import getLocal, setLocal
from httplib import CannotSendRequest, ResponseNotReady
from socket import error

logger = getLogger('collective.solr.manager')
marker = object()


class SolrConnectionConfig(Persistent):
    """ utility to hold the connection configuration for the solr server """
    implements(ISolrConnectionConfig)

    max_results = 0             # provide backwards compatibility
    required = []
    facets = []

    def __init__(self):
        self.active = False
        self.host = None
        self.port = None
        self.base = None
        self.async = False
        self.index_timeout = 0
        self.search_timeout = 0
        self.max_results = 0
        self.required = []
        self.facets = []

    def getId(self):
        """ return a unique id to be used with GenericSetup """
        return 'solr'


class SolrConnectionManager(object):
    """ a thread-local connection manager for solr """
    implements(ISolrConnectionManager)

    def __init__(self, active=None):
        if isinstance(active, bool):
            self.setHost(active=active)

    def setHost(self, active=False, host='localhost', port=8983, base='/solr'):
        """ set connection parameters """
        config = getUtility(ISolrConnectionConfig)
        config.active = active
        config.host = host
        config.port = port
        config.base = base
        self.closeConnection(clearSchema=True)

    def closeConnection(self, clearSchema=False):
        """ close the current connection, if any """
        logger.debug('closing connection')
        conn = getLocal('connection')
        if conn is not None:
            conn.close()
            setLocal('connection', None)
        if clearSchema:
            setLocal('schema', None)

    def getConnection(self, timeout=marker):
        """ returns an existing connection or opens one, optionally
            allowing to directly specify a timeout value """
        config = getUtility(ISolrConnectionConfig)
        if not config.active:
            return None
        conn = getLocal('connection')
        if conn is None and config.host is not None:
            host = '%s:%d' % (config.host, config.port)
            logger.debug('opening connection to %s', host)
            conn = SolrConnection(host=host, solrBase=config.base,
                persistent=True)
            setLocal('connection', conn)
        if conn is not None and timeout is not marker:
            conn.setTimeout(timeout)
        return conn

    def getSchema(self):
        """ returns the currently used schema or fetches it """
        schema = getLocal('schema')
        if schema is None:
            conn = self.getConnection()
            if conn is not None:
                logger.debug('getting schema from solr')
                try:
                    schema = conn.getSchema()
                    setLocal('schema', schema)
                except (error, CannotSendRequest, ResponseNotReady):
                    logger.exception('exception while getting schema')
        return schema

    def setTimeout(self, timeout):
        """ set the timeout on the current (or to be opened) connection
            to the given value """
        conn = self.getConnection()
        if conn is not None:
            conn.setTimeout(timeout)

    def setIndexTimeout(self):
        """ set the timeout on the current (or to be opened) connection
            to the value specified for indexing operations """
        config = getUtility(ISolrConnectionConfig)
        self.setTimeout(config.index_timeout or None)

    def setSearchTimeout(self):
        """ set the timeout on the current (or to be opened) connection
            to the value specified for search operations """
        config = getUtility(ISolrConnectionConfig)
        self.setTimeout(config.search_timeout or None)
