from time import time, clock
from zope.interface import implements
from zope.component import queryUtility
from Products.Five.browser import BrowserView
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.Archetypes.CatalogMultiplex import CatalogMultiplex

from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.interfaces import ISolrMaintenanceView


def indexable(obj):
    """ indicate whether a given object should be indexed; for now only
        objects inheriting one of the catalog mixin classes are considerd """
    return isinstance(obj, CatalogMultiplex) or isinstance(obj, CMFCatalogAware)


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
        proc = queryUtility(ISolrIndexQueueProcessor, name='solr')
        log = self.request.RESPONSE.write
        self.count = 0
        self.commit = batch
        def index(obj, path):
            global count
            if indexable(obj):
                log('indexing %r\n' %  obj)
                proc.index(obj)
                self.count += 1
                self.commit -= 1
                if self.commit == 0:
                    proc.commit()
                    self.commit = batch
        now, cpu = time(), clock()
        self.context.ZopeFindAndApply(self.context, search_sub=True,
            apply_func=index)
        proc.commit()   # make sure to commit in the end...
        now, cpu = time() - now, clock() - cpu
        log('solr index rebuilt.')
        log('indexed %d object(s) in %.3f seconds (%.3f cpu time).' % (self.count, now, cpu))

