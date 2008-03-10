from logging import getLogger
from persistent import Persistent
from DateTime import DateTime
from zope.interface import implements
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.solr import SolrConnection, SolrException
from collective.solr.local import getLocal, setLocal

logger = getLogger('collective.solr.indexer')


def datehandler(value):
    # TODO: we might want to handle datetime and time as well;
    # check the enfold.solr implementation
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        value = '%04d-%02d-%02dT%02d:%02d:%06.3fZ' % (v.year(),
            v.month(), v.day(), v.hour(), v.minute(), v.second())
    return value


handlers = {'solr.DateField': datehandler}


class SolrIndexQueueProcessor(Persistent):
    """ a queue processor for solr """
    implements(ISolrIndexQueueProcessor)

    def __init__(self, active=False):
        self.setHost(active=active)

    def index(self, obj, attributes=None):
        conn = self.getConnection()
        if conn is not None:
            data = self.getData(obj, attributes)
            self.prepareData(data)
            try:
                logger.debug('indexing %r (%r)', obj, data)
                conn.add(**data)
            except SolrException, e:
                logger.exception('exception during index')

    def reindex(self, obj, attributes=None):
        self.index(obj, attributes)

    def unindex(self, obj):
        conn = self.getConnection()
        if conn is not None:
            data = self.getData(obj, attributes=['id'])
            self.prepareData(data)
            # TODO: perhaps we should consider <uniqueKey> here
            assert data.has_key('id'), "no id in object data"
            try:
                logger.debug('unindexing %r (%r)', obj, data)
                conn.delete(id=data['id'])
            except SolrException, e:
                logger.exception('exception during delete')

    def begin(self):
        pass

    def commit(self):
        conn = self.getConnection()
        if conn is not None:
            try:
                logger.debug('committing')
                conn.commit()
            except SolrException, e:
                logger.exception('exception during commit')
            self.closeConnection()

    # helper methods

    def getData(self, obj, attributes=None):
        schema = self.getSchema()
        if schema is None:
            return {}
        if attributes is None:
            attributes = schema.keys()
        data, marker = {}, []
        for name in attributes:
            value = getattr(obj, name, marker)
            if value is marker:
                continue
            if callable(value):
                value = value()
            handler = handlers.get(schema[name].class_, None)
            if handler is not None:
                value = handler(value)
            data[name] = value
        return data

    def prepareData(self, data):
        """ modify data according to solr specifics, i.e. replace ':' by '$'
            for "allowedRolesAndUsers" etc """
        allowed = data.get('allowedRolesAndUsers', None)
        if allowed is not None:
            data['allowedRolesAndUsers'] = [r.replace(':','$') for r in allowed]

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
        """ returns the currently used schema of fetches it;
            TODO: move schema handling (multi-value etc) into `SolrConnection` """
        schema = getLocal('schema')
        if schema is None:
            conn = self.getConnection()
            if conn is not None:
                logger.debug('getting schema from solr')
                schema = conn.getSchema()
                setLocal('schema', schema)
        return schema

