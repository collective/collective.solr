from logging import getLogger
from persistent import Persistent
from zope.interface import implements
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.solr import SolrConnection
from collective.solr.local import getLocal, setLocal

logger = getLogger('collective.solr.manager')


class SolrConnectionManager(Persistent):
    """ a thread-local connection manager for solr """
    implements(ISolrConnectionManager)

    def __init__(self, active=False):
        self.setHost(active=active)

    def setHost(self, active=False, host='localhost', port=8983, base='/solr'):
        """ set connection parameters """
        self.active = active
        self.host = host
        self.port = port
        self.base = base
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

    def getConnection(self):
        """ returns an existing connection or opens one """
        if not self.active:
            return None
        conn = getLocal('connection')
        if conn is None and self.host is not None:
            host = '%s:%d' % (self.host, self.port)
            logger.debug('opening connection to %s', host)
            conn = SolrConnection(host=host, solrBase=self.base, persistent=True)
            setLocal('connection', conn)
        return conn

    def getSchema(self):
        """ returns the currently used schema or fetches it """
        schema = getLocal('schema')
        if schema is None:
            conn = self.getConnection()
            if conn is not None:
                logger.debug('getting schema from solr')
                schema = conn.getSchema()
                setLocal('schema', schema)
        return schema

