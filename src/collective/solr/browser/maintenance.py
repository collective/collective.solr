from logging import getLogger
from time import time, clock, strftime

from BTrees.IIBTree import IITreeSet
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from zope.interface import implements
from zope.component import queryUtility

from collective.indexing.indexer import getOwnIndexMethod
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrMaintenanceView
from collective.solr.indexer import indexable, SolrIndexProcessor
from collective.solr.indexer import boost_values
from collective.solr.parser import parse_date_as_datetime
from collective.solr.parser import SolrResponse
from collective.solr.parser import unmarshallers
from collective.solr.utils import findObjects
from collective.solr.utils import prepareData


logger = getLogger('collective.solr.maintenance')
MAX_ROWS = 1000000000


def timer(func=time):
    """ set up a generator returning the elapsed time since the last call """
    def gen(last=func()):
        while True:
            elapsed = func() - last
            last = func()
            yield '%.3fs' % elapsed
    return gen()


def checkpointIterator(function, interval=100):
    """ the iterator will call the given function for every nth invocation """
    counter = 0
    while True:
        counter += 1
        if counter % interval == 0:
            function()
        yield None


def notimeout(func):
    """ decorator to prevent long-running solr tasks from timing out """
    def wrapper(*args, **kw):
        """ wrapper with random docstring so ttw access still works """
        manager = queryUtility(ISolrConnectionManager)
        manager.setTimeout(None, lock=True)
        try:
            return func(*args, **kw)
        finally:
            manager.setTimeout(None, lock=False)
    return wrapper


class SolrMaintenanceView(BrowserView):
    """ helper view for indexing all portal content in Solr """
    implements(ISolrMaintenanceView)

    def mklog(self):
        """ helper to prepend a time stamp to the output """
        write = self.request.RESPONSE.write
        def log(msg, timestamp=True):
            if timestamp:
                msg = strftime('%Y/%m/%d-%H:%M:%S ') + msg
            write(msg)
        return log

    def optimize(self):
        """ optimize solr indexes """
        manager = queryUtility(ISolrConnectionManager)
        conn = manager.getConnection()
        conn.setTimeout(None)
        conn.commit(optimize=True)
        return 'solr indexes optimized.'

    def clear(self):
        """ clear all data from solr, i.e. delete all indexed objects """
        manager = queryUtility(ISolrConnectionManager)
        uniqueKey = manager.getSchema().uniqueKey
        conn = manager.getConnection()
        conn.setTimeout(None)
        conn.deleteByQuery('%s:[* TO *]' % uniqueKey)
        conn.commit()
        return 'solr index cleared.'

    def reindex(self, batch=1000, skip=0):
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """
        manager = queryUtility(ISolrConnectionManager)
        proc = SolrIndexProcessor(manager)
        conn = manager.getConnection()
        zodb_conn = self.context._p_jar
        log = self.mklog()
        log('reindexing solr catalog...\n')
        if skip:
            log('skipping indexing of %d object(s)...\n' % skip)
        real = timer()          # real time
        lap = timer()           # real lap time (for intermediate commits)
        cpu = timer(clock)      # cpu time
        processed = 0
        schema = manager.getSchema()
        key = schema.uniqueKey
        updates = {}            # list to hold data to be updated
        flush = lambda: conn.flush()
        flush = notimeout(flush)
        def checkPoint():
            for boost_values, data in updates.values():
                conn.add(boost_values=boost_values, **data)
            updates.clear()
            msg = 'intermediate commit (%d items processed, ' \
                  'last batch in %s)...\n' % (processed, lap.next())
            log(msg)
            logger.info(msg)
            flush()
            zodb_conn.cacheGC()
        cpi = checkpointIterator(checkPoint, batch)
        count = 0
        for path, obj in findObjects(self.context):
            if indexable(obj):
                if getOwnIndexMethod(obj, 'indexObject') is not None:
                    log('skipping indexing of %r via private method.\n' % obj)
                    continue
                count += 1
                if count <= skip:
                    continue
                data, missing = proc.getData(obj)
                prepareData(data)
                if not missing:
                    value = data.get(key, None)
                    if value is not None:
                        updates[value] = (boost_values(obj, data), data)
                        processed += 1
                        cpi.next()
                else:
                    log('missing data, skipping indexing of %r.\n' % obj)
        checkPoint()
        conn.commit()
        log('solr index rebuilt.\n')
        msg = 'processed %d items in %s (%s cpu time).'
        msg = msg % (processed, real.next(), cpu.next())
        log(msg)
        logger.info(msg)

    def sync(self, batch=1000):
        """Sync the Solr index with the portal catalog. Records contained
        in the catalog but not in Solr will be indexed and records not
        contained in the catalog will be removed.
        """
        manager = queryUtility(ISolrConnectionManager)
        proc = SolrIndexProcessor(manager)
        conn = manager.getConnection()
        key = queryUtility(ISolrConnectionManager).getSchema().uniqueKey
        zodb_conn = self.context._p_jar
        catalog = getToolByName(self.context, 'portal_catalog')
        getIndex = catalog._catalog.getIndex
        modified_index = getIndex('modified')
        uid_index = getIndex(key)
        log = self.mklog()
        real = timer()          # real time
        lap = timer()           # real lap time (for intermediate commits)
        cpu = timer(clock)      # cpu time
        # get Solr status
        query = '+%s:[* TO *]' % key
        response = conn.search(q=query, rows=MAX_ROWS, fl='%s modified' % key)
        # avoid creating DateTime instances
        simple_unmarshallers = unmarshallers.copy()
        simple_unmarshallers['date'] = parse_date_as_datetime
        flares = SolrResponse(response, simple_unmarshallers)
        response.close()
        solr_results = {}
        solr_uids = set()
        def _utc_convert(value):
            t_tup = value.utctimetuple()
            return ((((t_tup[0] * 12 + t_tup[1]) * 31 + t_tup[2])
                      * 24 + t_tup[3]) * 60 + t_tup[4])
        for flare in flares:
            uid = flare[key]
            solr_uids.add(uid)
            solr_results[uid] = _utc_convert(flare['modified'])
        # get catalog status
        cat_results = {}
        cat_uids = set()
        for uid, rid in uid_index._index.items():
            cat_uids.add(uid)
            cat_results[uid] = rid
        # differences
        index = cat_uids.difference(solr_uids)
        solr_uids.difference_update(cat_uids)
        unindex = solr_uids
        processed = 0
        flush = notimeout(lambda: conn.flush())
        def checkPoint():
            msg = 'intermediate commit (%d items processed, ' \
                  'last batch in %s)...\n' % (processed, lap.next())
            log(msg)
            logger.info(msg)
            flush()
            zodb_conn.cacheGC()
        cpi = checkpointIterator(checkPoint, batch)
        # Look up objects
        uid_rid_get = cat_results.get
        rid_path_get = catalog._catalog.paths.get
        catalog_traverse = catalog.unrestrictedTraverse
        def lookup(uid, rid=None,
                   uid_rid_get=uid_rid_get, rid_path_get=rid_path_get,
                   catalog_traverse=catalog_traverse):
            if rid is None:
                rid = uid_rid_get(uid)
            if not rid:
                return None
            if not isinstance(rid, int):
                rid = tuple(rid)[0]
            path = rid_path_get(rid)
            if not path:
                return None
            try:
                obj = catalog_traverse(path)
            except AttributeError:
                return None
            return obj
        log('processing %d "unindex" operations next...\n' % len(unindex))
        op = notimeout(lambda uid: conn.delete(id=uid))
        for uid in unindex:
            obj = lookup(uid)
            if obj is None:
                op(uid)
                processed += 1
                cpi.next()
            else:
                log('not unindexing existing object %r.\n' % uid)
        log('processing %d "index" operations next...\n' % len(index))
        op = notimeout(lambda obj: proc.index(obj))
        for uid in index:
            obj = lookup(uid)
            if indexable(obj):
                op(obj)
                processed += 1
                cpi.next()
            else:
                log('not indexing unindexable object %r.\n' % uid)
            if obj is not None:
                obj._p_deactivate()
        log('processing "reindex" operations next...\n')
        op = notimeout(lambda obj: proc.reindex(obj))
        cat_mod_get = modified_index._unindex.get
        solr_mod_get = solr_results.get
        done = unindex.union(index)
        for uid, rid in cat_results.items():
            if uid in done:
                continue
            if isinstance(rid, IITreeSet):
                rid = rid.keys()[0]
            if cat_mod_get(rid) != solr_mod_get(uid):
                obj = lookup(uid, rid=rid)
                if indexable(obj):
                    op(obj)
                    processed += 1
                    cpi.next()
                else:
                    log('not reindexing unindexable object %r.\n' % uid)
                if obj is not None:
                    obj._p_deactivate()
        conn.commit()
        log('solr index synced.\n')
        msg = 'processed %d object(s) in %s (%s cpu time).'
        msg = msg % (processed, real.next(), cpu.next())
        log(msg)
        logger.info(msg)
