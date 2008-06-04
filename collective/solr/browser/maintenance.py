from logging import getLogger
from time import time, clock
from zope.interface import implements
from zope.component import queryUtility
from Products.Five.browser import BrowserView
from httplib import BadStatusLine

from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.interfaces import ISolrMaintenanceView
from collective.solr.indexer import indexable

logger = getLogger('collective.solr.maintenance')


class SolrMaintenanceView(BrowserView):
    """ helper view for indexing all portal content in Solr """
    implements(ISolrMaintenanceView)

    def clear(self):
        """ clear all data from solr, i.e. delete all indexed objects """
        manager = queryUtility(ISolrConnectionManager)
        uniqueKey = manager.getSchema().uniqueKey
        conn = manager.getConnection()
        conn.deleteByQuery('%s:[* TO *]' % uniqueKey)
        conn.commit()
        return 'solr index cleared.'

    def reindex(self, batch=100):
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """
        manager = queryUtility(ISolrConnectionManager)
        proc = queryUtility(ISolrIndexQueueProcessor, name='solr')
        log = self.request.RESPONSE.write
        self.count = 0
        self.commit = batch
        def index(obj, path):
            global count
            if indexable(obj):
                log('indexing %r' % obj)
                lap = time()
                try:
                    proc.index(obj)
                except BadStatusLine:
                    log('WARNING: error while indexing %r' % obj)
                    logger.exception('error while indexing %r', obj)
                    manager.getConnection().reset()     # force new connection
                log(' (%.4fs)\n' % (time() - lap))
                self.count += 1
                self.commit -= 1
                if self.commit == 0:
                    log('intermediate commit (%d objects indexed)...\n' % self.count)
                    proc.commit()
                    self.commit = batch
                    manager.getConnection().reset()     # force new connection
        now, cpu = time(), clock()
        self.context.ZopeFindAndApply(self.context, search_sub=True,
            apply_func=index)
        proc.commit()   # make sure to commit in the end...
        now, cpu = time() - now, clock() - cpu
        log('solr index rebuilt.\n')
        msg = 'indexed %d object(s) in %.3f seconds (%.3f cpu time).' % (self.count, now, cpu)
        log(msg)
        logger.info(msg)

