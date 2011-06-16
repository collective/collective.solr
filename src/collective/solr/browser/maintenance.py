from logging import getLogger
from time import time, clock, strftime

from zope.interface import implements
from zope.component import queryUtility
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from collective.indexing.indexer import getOwnIndexMethod
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrMaintenanceView
from collective.solr.interfaces import ISearch
from collective.solr.indexer import indexable, SolrIndexProcessor
from collective.solr.indexer import boost_values
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

    def reindex(self, batch=1000, skip=0, cache=50000):
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """
        manager = queryUtility(ISolrConnectionManager)
        proc = SolrIndexProcessor(manager)
        conn = manager.getConnection()
        db = self.context.getPhysicalRoot()._p_jar.db()
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
            if cache:
                size = db.cacheSize()
                if size > cache:
                    log('minimizing zodb cache with %d objects...\n' % size)
                    db.cacheMinimize()
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

    def metadata(self, index, key, func=lambda x: x):
        """ build a mapping between a unique key and a given attribute from
            the portal catalog; catalog metadata must exist for the given
            index """
        catalog = getToolByName(self.context, 'portal_catalog')
        cat = catalog._catalog      # get the real catalog...
        pos = cat.schema[index]
        data = {}
        for uid, rids in cat.getIndex(key).items():
            for rid in rids:
                value = cat.data[rid][pos]
                if value is not None:
                    data[uid] = func(value)
        return data

    def diff(self):
        """ determine objects that need to be indexed/reindex/unindexed by
            diff'ing the records in the portal catalog and solr """
        key = queryUtility(ISolrConnectionManager).getSchema().uniqueKey
        uids = self.metadata('modified', key=key,
            func=lambda x: x.millis())
        search = queryUtility(ISearch)
        reindex = []
        rows = len(uids) * 10               # sys.maxint makes solr choke :(
        query = '+%s:[* TO *]' % key
        for flare in search(query, rows=rows, fl='%s modified' % key):
            uid = getattr(flare, key)
            assert uid, 'empty unique key?'
            if uid in uids:
                if uids[uid] > flare.modified.millis():
                    reindex.append(uid)     # item isn't current
                del uids[uid]               # remove from the list in any case
        return reindex

    def sync(self, batch=1000, cache=50000):
        """Sync the Solr index with the portal catalog. Records contained
        in the catalog but not in Solr will be indexed and records not
        contained in the catalog will be removed.
        """
        manager = queryUtility(ISolrConnectionManager)
        proc = SolrIndexProcessor(manager)
        conn = manager.getConnection()
        db = self.context.getPhysicalRoot()._p_jar.db()
        log = self.mklog()
        real = timer()          # real time
        lap = timer()           # real lap time (for intermediate commits)
        cpu = timer(clock)      # cpu time
        # get Solr status
        search = queryUtility(ISearch)
        key = queryUtility(ISolrConnectionManager).getSchema().uniqueKey
        query = '+%s:[* TO *]' % key
        flares = search(query, rows=MAX_ROWS, fl='%s modified' % key)
        solr_results = {}
        solr_uids = set()
        for flare in flares:
            uid = flare[key]
            solr_uids.add(uid)
            # TODO the search creates DateTime instances from the XML, we
            # don't need that overhead
            solr_results[uid] = flare['modified'].millis()
        # get catalog status
        catalog = getToolByName(self.context, 'portal_catalog')
        cat_uids = set(catalog._catalog.getIndex(key)._index.keys())
        # differences
        index = cat_uids.difference(solr_uids)
        solr_uids.difference_update(cat_uids)
        unindex = solr_uids

        # unoptimized
        reindex = self.diff()

        processed = 0
        flush = notimeout(lambda: conn.flush())
        def checkPoint():
            msg = 'intermediate commit (%d items processed, ' \
                  'last batch in %s)...\n' % (processed, lap.next())
            log(msg)
            logger.info(msg)
            flush()
            if cache:
                size = db.cacheSize()
                if size > cache:
                    log('minimizing zodb cache with %d objects...\n' % size)
                    db.cacheMinimize()
        cpi = checkpointIterator(checkPoint, batch)
        lookup = getToolByName(self.context, 'reference_catalog').lookupObject
        log('processing %d "index" operations next...\n' % len(index))
        op = notimeout(lambda obj: proc.index(obj))
        for uid in index:
            obj = lookup(uid)
            if indexable(obj):
                op(obj)
                processed += 1
                cpi.next()
            else:
                log('not indexing unindexable object %r.\n' % obj)
        log('processing %d "reindex" operations next...\n' % len(reindex))
        op = notimeout(lambda obj: proc.reindex(obj))
        for uid in reindex:
            obj = lookup(uid)
            if indexable(obj):
                op(obj)
                processed += 1
                cpi.next()
            else:
                log('not reindexing unindexable object %r.\n' % obj)
        log('processing %d "unindex" operations next...\n' % len(unindex))
        op = notimeout(lambda uid: conn.delete(id=uid))
        for uid in unindex:
            obj = lookup(uid)
            if obj is None:
                op(uid)
                processed += 1
                cpi.next()
            else:
                log('not unindexing existing object %r (%r).\n' % (obj, uid))
        conn.commit()
        log('solr index synced.\n')
        msg = 'processed %d object(s) in %s (%s cpu time).'
        msg = msg % (processed, real.next(), cpu.next())
        log(msg)
        logger.info(msg)
