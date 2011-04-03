from logging import getLogger
from Acquisition import aq_get
from DateTime import DateTime
from datetime import date, datetime
from zope.component import getUtility, queryUtility, queryMultiAdapter
from zope.interface import implements
from ZODB.POSException import ConflictError
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
        objects inheriting one of the catalog mixin classes are considered """
    return isinstance(obj, CatalogMultiplex) or \
        isinstance(obj, CMFCatalogAware)


def datehandler(value):
    # TODO: we might want to handle datetime and time as well;
    # check the enfold.solr implementation
    if value is None:
        raise AttributeError
    if isinstance(value, str) and not value.endswith('Z'):
        value = DateTime(value)
    if isinstance(value, DateTime):
        v = value.toZone('UTC')
        value = '%04d-%02d-%02dT%02d:%02d:%06.3fZ' % (v.year(),
            v.month(), v.day(), v.hour(), v.minute(), v.second())
    elif isinstance(value, date):
        # Convert a timezone aware timetuple to a non timezone aware time
        # tuple representing utc time. Does nothing if object is not
        # timezone aware
        value = datetime(*value.utctimetuple()[:7])
        value = '%s.%03dZ' % (value.strftime('%Y-%m-%dT%H:%M:%S'), value.microsecond % 1000)
    return value


handlers = {
    'solr.DateField': datehandler,
    'solr.TrieDateField': datehandler,
}


def boost_values(obj, data):
    """ calculate boost values using a method or skin script;  returns
        a dictionary with the values or `None` """
    boost_index_getter = aq_get(obj, 'solr_boost_index_values', None)
    if boost_index_getter is not None:
        return boost_index_getter(data)


class SolrIndexProcessor(object):
    """ a queue processor for solr """
    implements(ISolrIndexQueueProcessor)

    def __init__(self, manager=None):
        self.manager = manager

    def index(self, obj, attributes=None):
        conn = self.getConnection()
        if conn is not None and indexable(obj):
            # unfortunately with current versions of solr we need to provide
            # data for _all_ fields during an <add> -- partial updates aren't
            # supported (see https://issues.apache.org/jira/browse/SOLR-139)
            # however, the reindexing can be skipped if none of the given
            # attributes match existing solr indexes...
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
            if attributes is not None:
                attributes = set(schema.keys()).intersection(attributes)
                if not attributes:
                    return
            data, missing = self.getData(obj)
            if not data:
                return          # don't index with no data...
            prepareData(data)
            if data.get(uniqueKey, None) is not None and not missing:
                config = getUtility(ISolrConnectionConfig)
                if config.commit_within:
                    data['commitWithin'] = config.commit_within
                try:
                    logger.debug('indexing %r (%r)', obj, data)
                    conn.add(boost_values=boost_values(obj, data), **data)
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
            config = getUtility(ISolrConnectionConfig)
            if not isinstance(wait, bool):
                wait = not config.async
            try:
                logger.debug('committing')
                if not config.auto_commit or config.commit_within:
                    # If we have commitWithin enabled, we never want to do
                    # explicit commits. Even though only add's support this
                    # and we might wait a bit longer on delete's this way
                    conn.flush()
                else:
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
        if attributes is None:
            attributes = schema.keys()
        obj = self.wrapObject(obj)
        data, marker = {}, []
        for name in attributes:
            try:
                value = getattr(obj, name)
                if callable(value):
                    value = value()
            except ConflictError:
                raise
            except AttributeError:
                continue
            except Exception:
                logger.exception('Error occured while getting data for '
                    'indexing!')
                continue
            field = schema[name]
            handler = handlers.get(field.class_, None)
            if handler is not None:
                try:
                    value = handler(value)
                except AttributeError:
                    continue
            elif isinstance(value, (list, tuple)) and not field.multiValued:
                separator = getattr(field, 'separator', ' ')
                value = separator.join(value)
            data[name] = value
        missing = set(schema.requiredFields) - set(data.keys())
        return data, missing
