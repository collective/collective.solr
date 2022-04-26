from datetime import date, datetime
from logging import getLogger
from socket import error

import six
from Acquisition import aq_get
from collective.solr.exceptions import SolrConnectionException
from collective.solr.interfaces import (
    ICheckIndexable,
    ISolrAddHandler,
    ISolrConnectionManager,
    ISolrIndexQueueProcessor,
)
from collective.solr.utils import getConfig, prepareData
from DateTime import DateTime
from lxml import etree
from plone.indexer.interfaces import IIndexableObject, IIndexableObjectWrapper
from plone.registry.interfaces import IRegistry
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.utils import getToolByName
from requests_toolbelt import MultipartEncoder
from six.moves.urllib.parse import urlencode
from ZODB.interfaces import BlobError
from ZODB.POSException import ConflictError
from zope.component import (
    adapts,
    getUtility,
    queryAdapter,
    queryMultiAdapter,
    queryUtility,
)
from zope.interface import Interface, implementer

logger = getLogger("collective.solr.indexer")


@implementer(ICheckIndexable)
class BaseIndexable(object):

    adapts(Interface)

    def __init__(self, context):
        self.context = context

    def __call__(self):
        return isinstance(self.context, CMFCatalogAware)


def datehandler(value):
    # TODO: we might want to handle datetime and time as well;
    # check the enfold.solr implementation
    if value is None or value == "":
        raise AttributeError
    if isinstance(value, str) and not value.endswith("Z"):
        try:
            value = DateTime(value)
        except SyntaxError:
            raise AttributeError

    if isinstance(value, DateTime):
        v = value.toZone("UTC")
        value = "%04d-%02d-%02dT%02d:%02d:%02d.%03dZ" % (
            v.year(),
            v.month(),
            v.day(),
            v.hour(),
            v.minute(),
            int(v.second()),
            v.millis() % 1000,
        )
    elif isinstance(value, datetime):
        # Convert a timezone aware timetuple to a non timezone aware time
        # tuple representing utc time. Does nothing if object is not
        # timezone aware
        millis = int(
            value.microsecond / 1000
        )  # 1 second = 1 000 millis = 1 000 000 microsecond
        value = datetime(*value.utctimetuple()[:6])
        value = "%s.%03dZ" % (value.strftime("%Y-%m-%dT%H:%M:%S"), millis)
    elif isinstance(value, date):
        value = "%s.000Z" % value.strftime("%Y-%m-%dT%H:%M:%S")
    return value


def inthandler(value):
    if value is None or value == "":
        raise AttributeError("Solr cant handle none strings or empty values")
    else:
        return value


handlers = {
    "solr.DateField": datehandler,
    "solr.DatePointField": datehandler,
    "solr.FloatField": inthandler,
    "solr.FloatPointField": inthandler,
    "solr.TrieDateField": datehandler,
    "solr.TrieIntField": inthandler,
    "solr.IntField": inthandler,
    "solr.IntPointField": inthandler,
}


@implementer(ISolrAddHandler)
class DefaultAdder(object):
    """"""

    def __init__(self, context):
        self.context = context

    def __call__(self, conn, **data):
        # remove in Plone unused field links,
        # which gives problems with some documents
        data.pop("links", "")
        conn.add(**data)


class BinaryAdder(DefaultAdder):
    """Add binary content to index via tika"""

    def getblob(self):
        field = self.context.getPrimaryField()
        # do not return anything if a content object does not provide a primary field
        if not field:
            return
        return field.get(self.context).blob

    def getpath(self):
        blob = self.getblob()
        if blob is None:
            return None
        try:
            path = blob.committed()
        except BlobError:
            path = blob._p_blob_committed or blob._p_blob_uncommitted
        logger.debug("Indexing BLOB from path %s", path)
        return path

    def __call__(self, conn, **data):
        postdata = {}
        path = self.getpath()
        if path is None:
            super(BinaryAdder, self).__call__(conn, **data)

        postdata["extractFormat"] = "text"
        postdata["extractOnly"] = "true"
        postdata["wt"] = "xml"
        headers = conn.formheaders

        registry = getUtility(IRegistry)
        use_tika = registry.get("collective.solr.use_tika")
        tika_default_field = registry.get("collective.solr.tika_default_field")
        if not use_tika:
            # fall back to use SearchableText if tika is not enabled
            tika_default_field = "SearchableText"

        # blobs are accessed via the file system
        if use_tika:
            blob = self.getblob()
            if blob is None:
                return
            openedBlob = blob.open()

            postdata["myfile"] = (
                data["id"],
                openedBlob,
                data.get("content_type", "application/octet-stream"),
            )

            encodedPost = MultipartEncoder(fields=postdata)

            headers["Content-Type"] = encodedPost.content_type
            postdata_urlencoded = encodedPost.to_string()
        else:
            postdata["stream.file"] = self.getpath()
            postdata["stream.contentType"] = data.get(
                "content_type", "application/octet-stream"
            )
            postdata_urlencoded = urlencode(postdata, doseq=True)

        url = "%s/update/extract" % conn.solrBase

        try:
            response = conn.doPost(url, postdata_urlencoded, headers)
            root = etree.parse(response)
            data[tika_default_field] = root.find(".//str").text.strip()
        except SolrConnectionException as e:
            logger.warn("Error %s @ %s", e, data["path_string"])
            data[tika_default_field] = ""
        except etree.XMLSyntaxError as e:
            logger.warn("Parsing error %s @ %s.", e, data["path_string"])
            data[tika_default_field] = ""
        finally:
            if use_tika:
                openedBlob.close()

        super(BinaryAdder, self).__call__(conn, **data)


class DXFileBinaryAdder(BinaryAdder):

    fieldname = "file"

    def getblob(self):
        field = getattr(self.context, self.fieldname, None)
        return getattr(field, "_blob", None)


class DXImageBinaryAdder(DXFileBinaryAdder):

    fieldname = "image"


def boost_values(obj, data):
    """calculate boost values using a method or skin script;  returns
    a dictionary with the values or `None`"""
    boost_index_getter = aq_get(obj, "solr_boost_index_values", None)
    if boost_index_getter is not None:
        return boost_index_getter(data)


@implementer(ISolrIndexQueueProcessor)
class SolrIndexProcessor(object):
    """a queue processor for solr"""

    def __init__(self, manager=None):
        self.manager = manager

    def index(self, obj, attributes=None):
        """Index the specified attributes for obj using atomic updates, or all
        of them if `attributes` is `None`.
        Also make sure the `uniqueKey` is part of attributes, and passing the
        attributes to the self.getData() call to avoid causing Plone to index
        all fields instead of just the necessary ones.
        """
        conn = self.getConnection()
        if conn is not None and ICheckIndexable(obj)():
            schema = self.manager.getSchema()
            if schema is None:
                msg = "unable to fetch schema, skipping indexing of %r"
                logger.warning(msg, obj)
                return
            uniqueKey = schema.get("uniqueKey", None)
            if uniqueKey is None:
                msg = "schema is missing unique key, skipping indexing of %r"
                logger.warning(msg, obj)
                return

            if attributes:

                if "path" in attributes:
                    attributes = list(attributes)
                    attributes.extend(["path_string", "path_parents", "path_depth"])

                attributes = set(schema.keys()).intersection(attributes)
                if not attributes:
                    return

                if uniqueKey not in attributes:
                    # The uniqueKey is required in order to identify the
                    # document when doing atomic updates.
                    attributes.add(uniqueKey)

            data, missing = self.getData(obj, attributes=attributes)
            if not data:
                return  # don't index with no data...
            prepareData(data)
            if data.get(uniqueKey, None) is not None and not missing:
                registry = getUtility(IRegistry)
                config_commit_within = registry["collective.solr.commit_within"]  # noqa
                if config_commit_within:
                    data["commitWithin"] = config_commit_within
                try:
                    logger.debug("indexing %r (%r)", obj, data)
                    pt = data.get("portal_type", "default")
                    logger.debug("indexing %r with %r adder (%r)", obj, pt, data)

                    adder = queryAdapter(obj, ISolrAddHandler, name=pt)

                    if adder is None:
                        adder = DefaultAdder(obj)
                    adder(conn, boost_values=boost_values(obj, data), **data)
                except (SolrConnectionException, error):
                    logger.exception("exception during indexing %r", obj)

    def reindex(self, obj, attributes=None, update_metadata=False):
        if not attributes:
            attributes = None
        self.index(obj, attributes)

    def unindex(self, obj):
        conn = self.getConnection()
        if conn is not None:
            schema = self.manager.getSchema()
            if schema is None:
                msg = "unable to fetch schema, skipping unindexing of %r"
                logger.warning(msg, obj)
                return
            uniqueKey = schema.get("uniqueKey", None)
            if uniqueKey is None:
                msg = "schema is missing unique key, skipping unindexing of %r"
                logger.warning(msg, obj)
                return

            # remove the PathWrapper, otherwise IndexableObjectWrapper fails
            # to get the UID indexer (for dexterity objects) and the parent
            # UID is acquired
            if hasattr(obj, "context"):
                obj = obj.context

            data, missing = self.getData(obj, attributes=[uniqueKey])
            prepareData(data)
            if uniqueKey not in data:
                msg = "Can not unindex: no unique key for object %r"
                logger.info(msg, obj)
                return
            data_key = data[uniqueKey]
            if data_key is None:
                msg = "Can not unindex: `None` unique key for object %r"
                logger.info(msg, obj)
                return
            try:
                logger.debug("unindexing %r (%r)", obj, data)
                conn.delete(id=data_key)
            except (SolrConnectionException, error):
                logger.exception("exception during unindexing %r", obj)

    def begin(self):
        pass

    def commit(self, wait=None):
        conn = self.getConnection()
        if conn is not None:
            config = getConfig()
            if not isinstance(wait, bool):
                wait = not config.async_indexing
            try:
                logger.debug("committing")
                if not config.auto_commit or config.commit_within:
                    # If we have commitWithin enabled, we never want to do
                    # explicit commits. Even though only add's support this
                    # and we might wait a bit longer on delete's this way
                    conn.flush()
                else:
                    conn.commit(waitSearcher=wait)
            except (SolrConnectionException, error):
                logger.exception("exception during commit")
            self.manager.closeConnection()

    def abort(self):
        conn = self.getConnection()
        if conn is not None:
            logger.debug("aborting")
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
        """wrap object with an "IndexableObjectWrapper` (for Plone < 3.3) or
        adapt it to `IIndexableObject` (for Plone >= 3.3), see
        `CMFPlone...CatalogTool.catalog_object` for some background"""
        wrapper = obj
        # first try the new way, i.e. using `plone.indexer`...
        catalog = getToolByName(obj, "portal_catalog", None)
        adapter = queryMultiAdapter((obj, catalog), IIndexableObject)
        if adapter is not None:
            wrapper = adapter
        else:  # otherwise try the old way...
            portal = getToolByName(obj, "portal_url", None)
            if portal is None:
                return obj
            portal = portal.getPortalObject()
            adapter = queryMultiAdapter((obj, portal), IIndexableObjectWrapper)
            if adapter is not None:
                wrapper = adapter
            wft = getToolByName(obj, "portal_workflow", None)
            if wft is not None:
                wrapper.update(wft.getCatalogVariablesFor(obj))
        return wrapper

    def getData(self, obj, attributes=None):
        schema = self.manager.getSchema()
        if schema is None:
            return {}, ()
        if attributes is None:
            attributes = list(schema.keys())
        obj = self.wrapObject(obj)
        data = {}
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
                logger.exception("Error occured while getting data for indexing!")
                continue
            field = schema[name]
            handler = handlers.get(field.class_, None)
            if handler is not None:
                try:
                    value = handler(value)
                except AttributeError:
                    continue
            elif isinstance(value, (list, tuple)) and not field.multiValued:
                separator = getattr(field, "separator", " ")
                value = separator.join(value)
            if isinstance(value, six.binary_type):
                value = value.decode("utf-8")
            data[name] = value
        missing = set(schema.requiredFields) - set(data.keys())
        return data, missing
