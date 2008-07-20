from logging import getLogger
from persistent import Persistent
from DateTime import DateTime
from zope.component import getUtility, queryUtility, queryMultiAdapter
from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.Archetypes.CatalogMultiplex import CatalogMultiplex
from plone.app.content.interfaces import IIndexableObjectWrapper
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.solr import SolrException
from collective.solr.utils import prepareData
from socket import error

logger = getLogger('collective.solr.indexer')


def indexable(obj):
    """ indicate whether a given object should be indexed; for now only
        objects inheriting one of the catalog mixin classes are considerd """
    return isinstance(obj, CatalogMultiplex) or isinstance(obj, CMFCatalogAware)


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
        if conn is not None and indexable(obj):
            data, missing = self.getData(obj, attributes)
            prepareData(data)
            schema = self.manager.getSchema()
            if schema is None:
                logger.warning('unable to fetch schema, skipping indexing of %r', obj)
                return
            if data.get(schema['uniqueKey'], None) is not None and not missing:
                try:
                    logger.debug('indexing %r (%r)', obj, data)
                    conn.add(**data)
                except (SolrException, error):
                    logger.exception('exception during indexing %r', obj)

    def reindex(self, obj, attributes=None):
        self.index(obj, attributes)

    def unindex(self, obj):
        conn = self.getConnection()
        if conn is not None:
            schema = self.manager.getSchema()
            if schema is None:
                logger.warning('unable to fetch schema, skipping unindexing of %r', obj)
                return
            uniqueKey = schema['uniqueKey']
            data, missing = self.getData(obj, attributes=[uniqueKey])
            prepareData(data)
            if not data.has_key(uniqueKey):
                logger.info('Can not unindex: no unique key for object %r', obj)
                return
            data_key = data[uniqueKey]
            if data_key is None:
                logger.info('Can not unindex: `None` unique key for object %r', obj)
                return
            try:
                logger.debug('unindexing %r (%r)', obj, data)
                conn.delete(id=data_key)
            except (SolrException, error):
                logger.exception('exception during unindexing %r', obj)

    def begin(self):
        pass

    def commit(self, wait=None):
        conn = self.getConnection()
        if conn is not None:
            if not isinstance(wait, bool):
                wait = not getUtility(ISolrConnectionConfig).async
            try:
                logger.debug('committing')
                conn.commit(waitFlush=wait, waitSearcher=wait)
            except (SolrException, error):
                logger.exception('exception during commit')
            self.manager.closeConnection()

    # helper methods

    def getConnection(self):
        if self.manager is None:
            self.manager = queryUtility(ISolrConnectionManager)
        if self.manager is not None:
            self.manager.setIndexTimeout()
            return self.manager.getConnection()

    def wrapObject(self, obj):
        """ wrap object with an "IndexableObjectWrapper`, see
            `CatalogTool.catalog_object` for some background """
        portal = getToolByName(obj, 'portal_url', None)
        if portal is None:
            return obj
        portal = portal.getPortalObject()
        wrapper = queryMultiAdapter((obj, portal), IIndexableObjectWrapper)
        if wrapper is None:
            return obj
        wft = getToolByName(obj, 'portal_workflow', None)
        if wft is not None:
            wrapper.update(wft.getCatalogVariablesFor(obj))
        return wrapper

    def getData(self, obj, attributes=None):
        schema = self.manager.getSchema()
        if schema is None:
            return {}, ()
        if attributes is None:
            attributes = schema.keys()
        else:
            attributes = set(schema.keys()).intersection(set(attributes))
        obj = self.wrapObject(obj)
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
        missing = set(schema.requiredFields) - set(data.keys())
        return data, missing

