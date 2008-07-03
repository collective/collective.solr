from logging import getLogger
from time import time, clock
from zope.interface import implements
from zope.component import queryUtility
from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName
from httplib import BadStatusLine

from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.interfaces import ISolrMaintenanceView
from collective.solr.interfaces import ISearch
from collective.solr.indexer import indexable
from collective.solr.utils import findObjects

logger = getLogger('collective.solr.maintenance')


def timer(func=time):
    def gen(last=func()):
        while True:
            elapsed = func() - last
            last = func()
            yield '%.3fs' % elapsed
    return gen()


def checkpointIterator(function, interval=100):
    counter = 0
    while True:
        counter += 1
        if counter % interval == 0:
            function()
        yield None


class SolrMaintenanceView(BrowserView):
    """ helper view for indexing all portal content in Solr """
    implements(ISolrMaintenanceView)

    def optimize(self):
        """ optimize solr indexes """
        manager = queryUtility(ISolrConnectionManager)
        manager.getConnection().commit(optimize=True)
        return 'solr indexes optimized.'

    def clear(self):
        """ clear all data from solr, i.e. delete all indexed objects """
        manager = queryUtility(ISolrConnectionManager)
        uniqueKey = manager.getSchema().uniqueKey
        conn = manager.getConnection()
        conn.deleteByQuery('%s:[* TO *]' % uniqueKey)
        conn.commit()
        return 'solr index cleared.'

    def reindex(self, batch=100, skip=0, cache=1000, attributes=None):
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """
        manager = queryUtility(ISolrConnectionManager)
        proc = queryUtility(ISolrIndexQueueProcessor, name='solr')
        log = self.request.RESPONSE.write
        if skip:
            log('skipping indexing of %d object(s)...\n' % skip)
        now, cpu = time(), clock()
        count = 0
        indexed = 0
        commit = batch
        for path, obj in findObjects(self.context):
            if indexable(obj):
                count += 1
                if count <= skip:
                    continue
                log('indexing %r' % obj)
                lap = time()
                try:
                    proc.index(obj, attributes)
                    indexed += 1
                except BadStatusLine:
                    log('WARNING: error while indexing %r' % obj)
                    logger.exception('error while indexing %r', obj)
                    manager.getConnection().reset()     # force new connection
                log(' (%.4fs)\n' % (time() - lap))
                commit -= 1
                if commit == 0:
                    msg = 'intermediate commit (%d objects indexed in %.4fs)...\n'
                    log(msg %  (indexed, time() - now))
                    proc.commit(wait=True)
                    commit = batch
                    manager.getConnection().reset()     # force new connection
                    if cache:
                        db = self.context.getPhysicalRoot()._p_jar.db()
                        size = db.cacheSize()
                        if size > cache:
                            log('minimizing zodb cache with %d objects...\n' % size)
                            db.cacheMinimize()
        proc.commit(wait=True)      # make sure to commit in the end...
        now, cpu = time() - now, clock() - cpu
        log('solr index rebuilt.\n')
        msg = 'indexed %d object(s) in %.3f seconds (%.3f cpu time).' % (indexed, now, cpu)
        log(msg)
        logger.info(msg)

    def diff(self):
        """ determine objects that need to be indexed/reindex/unindexed by
            diff'ing the records in the portal catalog and solr """
        catalog = getToolByName(self.context, 'portal_catalog')
        uids = {}
        for brain in catalog():
            if brain.UID and brain.modified is not None:
                uids[brain.UID] = brain.modified.millis()
        search = queryUtility(ISearch)
        reindex = []
        unindex = []
        rows = len(uids) * 10               # sys.maxint makes solr choke :(
        for flare in search('UID:[* TO *]', rows=rows, fl='UID modified'):
            uid = flare.UID
            assert uid, 'empty UID?'
            if uids.has_key(uid):
                if uids[uid] > flare.modified.millis():
                    reindex.append(uid)     # item isn't current
                del uids[uid]               # remove from the list in any case
            else:
                unindex.append(uid)         # item doesn't exist in catalog
        index = uids.keys()
        return index, reindex, unindex

    def sync(self, batch=100, cache=1000):
        """ sync the solr index with the portal catalog;  records contained
            in the catalog but not in solr will be indexed and records not
            contained in the catalog can be optionally removed;  this can
            be used to ensure consistency between zope and solr after the
            solr server has been unavailable etc """
        manager = queryUtility(ISolrConnectionManager)
        proc = queryUtility(ISolrIndexQueueProcessor, name='solr')
        db = self.context.getPhysicalRoot()._p_jar.db()
        log = self.request.RESPONSE.write
        real = timer()          # real time
        lap = timer()           # real lap time (for intermediate commits)
        cpu = timer(clock)      # cpu time
        log('determining differences between portal catalog and solr...')
        index, reindex, unindex = self.diff()
        log(' (%s).\n' % lap.next())
        log('operations needed: %d "index", %d "reindex", %d "unindex"\n' % (
            len(index), len(reindex), len(unindex)))
        processed = 0
        def checkPoint():
            msg = 'intermediate commit (%d objects processed in %s)...\n'
            log(msg % (processed, lap.next()))
            proc.commit(wait=True)
            manager.getConnection().reset()     # force new connection
            if cache:
                size = db.cacheSize()
                if size > cache:
                    log('minimizing zodb cache with %d objects...\n' % size)
                    db.cacheMinimize()
        single = timer()        # real time for single object
        cpi = checkpointIterator(checkPoint, batch)
        lookup = getToolByName(self.context, 'reference_catalog').lookupObject
        log('processing %d "index" operations next...\n' % len(index))
        for uid in index:
            obj = lookup(uid)
            if indexable(obj):
                log('indexing %r' % obj)
                proc.index(obj)
                processed += 1
                log(' (%s).\n' % single.next())
                cpi.next()
        log('processing %d "reindex" operations next...\n' % len(reindex))
        for uid in reindex:
            obj = lookup(uid)
            if indexable(obj):
                log('reindexing %r' % obj)
                proc.reindex(obj)
                processed += 1
                log(' (%s).\n' % single.next())
                cpi.next()
        log('processing %d "unindex" operations next...\n' % len(unindex))
        conn = proc.getConnection()
        for uid in unindex:
            obj = lookup(uid)
            if obj is None:
                log('unindexing %r' % uid)
                conn.delete(id=uid)
                processed += 1
                log(' (%s).\n' % single.next())
                cpi.next()
            else:
                log('not unindexing existing object %r (%r).\n' % (obj, uid))
        proc.commit(wait=True)      # make sure to commit in the end...
        log('solr index synced.\n')
        msg = 'processed %d object(s) in %s (%s cpu time).'
        msg = msg % (processed, real.next(), cpu.next())
        log(msg)
        logger.info(msg)

