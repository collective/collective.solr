from logging import getLogger
from persistent import Persistent
from DateTime import DateTime
from zope.component import queryUtility
from zope.interface import implements
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.solr import SolrException

logger = getLogger('collective.solr.indexer')


def datehandler(value):
    # TODO: we might want to handle datetime and time as well;
    # check the enfold.solr implementation
    if isinstance(value, str) and not value.endswith('Z'):
        value = DateTime(value)
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        value = '%04d-%02d-%02dT%02d:%02d:%06.3fZ' % (v.year(),
            v.month(), v.day(), v.hour(), v.minute(), v.second())
    return value


handlers = {'solr.DateField': datehandler}


class SolrIndexQueueProcessor(Persistent):
    """ a queue processor for solr """
    implements(ISolrIndexQueueProcessor)

    def __init__(self, manager=None):
        self.manager = manager      # for testing purposes only

    def index(self, obj, attributes=None):
        conn = self.getConnection()
        if conn is not None:
            data = self.getData(obj, attributes)
            self.prepareData(data)
            schema = self.manager.getSchema()
            if data.get(schema['uniqueKey'], None) is not None:
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
            schema = self.manager.getSchema()
            uniqueKey = schema['uniqueKey']
            data = self.getData(obj, attributes=[uniqueKey])
            self.prepareData(data)
            assert data.has_key(uniqueKey), "no value for <uniqueKey> in object data"
            try:
                logger.debug('unindexing %r (%r)', obj, data)
                conn.delete(id=data[uniqueKey])
            except SolrException, e:
                logger.exception('exception during delete')

    def begin(self):
        self.manager = queryUtility(ISolrConnectionManager)

    def commit(self):
        conn = self.getConnection()
        if conn is not None:
            try:
                logger.debug('committing')
                conn.commit()
            except SolrException, e:
                logger.exception('exception during commit')
            self.manager.closeConnection()

    # helper methods

    def getConnection(self):
        if self.manager is None:
            self.manager = queryUtility(ISolrConnectionManager)
        if self.manager is not None:
            return self.manager.getConnection()

    def getData(self, obj, attributes=None):
        schema = self.manager.getSchema()
        if schema is None:
            return {}
        if attributes is None:
            attributes = schema.keys()
        else:
            attributes = set(schema.keys()).intersection(set(attributes))
        data, marker = {}, []
        for name in attributes:
            value = getattr(obj, name, marker)
            if value is marker:
                continue
            if callable(value):
                value = value()
            field = schema[name]
            handler = handlers.get(field.class_, None)
            if handler is not None:
                value = handler(value)
            elif isinstance(value, (list, tuple)) and not field.multiValued:
                separator = getattr(field, 'separator', ' ')
                value = separator.join(value)
            data[name] = value
        return data

    def prepareData(self, data):
        """ modify data according to solr specifics, i.e. replace ':' by '$'
            for "allowedRolesAndUsers" etc """
        allowed = data.get('allowedRolesAndUsers', None)
        if allowed is not None:
            data['allowedRolesAndUsers'] = [r.replace(':','$') for r in allowed]

