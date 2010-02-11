from logging import getLogger
from DateTime import DateTime
from zope.component import getUtility, queryUtility, queryMultiAdapter
from zope.interface import implements
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.Archetypes.CatalogMultiplex import CatalogMultiplex
from plone.app.content.interfaces import IIndexableObjectWrapper
from plone.indexer.interfaces import IIndexableObject

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
    return isinstance(obj, CatalogMultiplex) or \
        isinstance(obj, CMFCatalogAware)


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


class SolrIndexProcessor(object):
    """ a queue processor for solr """
    implements(ISolrIndexQueueProcessor)

    def __init__(self, manager=None):
        self.manager = manager

    def index(self, obj, attributes=None):
        conn = self.getConnection()
        if conn is not None and indexable(obj):
            data, missing = self.getData(obj, attributes)
            if not data:
                return          # don't index with no data...
            prepareData(data)
            schema = self.manager.getSchema()
            if schema is None:
                msg = 'unable to fetch schema, skipping indexing of %r'
                logger.warning(msg, obj)
                return
            uniqueKey = schema.get('uniqueKey', None)
            if uniqueKey is None:
                msg = 'schema is missing unique key, skipping indexing of %r'
                logger.warning(msg, obj)
                return
            if data.get(uniqueKey, None) is not None and not missing:
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
                msg = 'unable to fetch schema, skipping unindexing of %r'
                logger.warning(msg, obj)
                return
            uniqueKey = schema.get('uniqueKey', None)
            if uniqueKey is None:
                msg = 'schema is missing unique key, skipping unindexing of %r'
                logger.warning(msg, obj)
                return
            data, missing = self.getData(obj, attributes=[uniqueKey])
            prepareData(data)
            if not uniqueKey in data:
                msg = 'Can not unindex: no unique key for object %r'
                logger.info(msg, obj)
                return
            data_key = data[uniqueKey]
            if data_key is None:
                msg = 'Can not unindex: `None` unique key for object %r'
                logger.info(msg, obj)
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

    def abort(self):
        conn = self.getConnection()
        if conn is not None:
            logger.debug('aborting')
            conn.abort()
            self.manager.closeConnection()

    # helper methods

    def getConnection(self):
        if self.manager is None:
            self.manager = queryUtility(ISolrConnectionManager)
        if self.manager is not None:
            self.manager.setIndexTimeout()
            return self.manager.getConnection()

    def wrapObject(self, obj):
        """ wrap object with an "IndexableObjectWrapper` (for Plone < 3.3) or
            adapt it to `IIndexableObject` (for Plone >= 3.3), see
            `CMFPlone...CatalogTool.catalog_object` for some background """
        wrapper = obj
        # first try the new way, i.e. using `plone.indexer`...
        catalog = getToolByName(obj, 'portal_catalog', None)
        adapter = queryMultiAdapter((obj, catalog), IIndexableObject)
        if adapter is not None:
            wrapper = adapter
        else:       # otherwise try the old way...
            portal = getToolByName(obj, 'portal_url', None)
            if portal is None:
                return obj
            portal = portal.getPortalObject()
            adapter = queryMultiAdapter((obj, portal), IIndexableObjectWrapper)
            if adapter is not None:
                wrapper = adapter
            wft = getToolByName(obj, 'portal_workflow', None)
            if wft is not None:
                wrapper.update(wft.getCatalogVariablesFor(obj))
        return wrapper

    def getData(self, obj, attributes=None):
        schema = self.manager.getSchema()
        if schema is None:
            return {}, ()
        # unfortunately with current versions of solr we need to provide data
        # for _all_ fields during an <add>.  partial updates aren't supported
        # yet (see https://issues.apache.org/jira/browse/SOLR-139).  however,
        # the reindexing can be stopped if none of the given attributes match
        # existing solr indexes...
        if attributes is not None:
            if not set(schema.keys()).intersection(set(attributes)):
                return {}, ()
        attributes = schema.keys()
        obj = self.wrapObject(obj)
        data, marker = {}, []
        for name in attributes:
            try:
                value = getattr(obj, name)
                if callable(value):
                    value = value()
            except AttributeError:
                continue
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
