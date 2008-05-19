from zope.interface import implements
from zope.component import queryUtility
from Products.Five.browser import BrowserView
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.Archetypes.CatalogMultiplex import CatalogMultiplex
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.interfaces import ISolrMaintenanceView


def indexable(obj):
    """ indicate whether a given object should be indexed; for now only
        objects inheriting one of the catalog mixin classes are considerd """
    return isinstance(obj, CatalogMultiplex) or isinstance(obj, CMFCatalogAware)


class SolrMaintenanceView(BrowserView):
    """ helper view for indexing all portal content in Solr """
    implements(ISolrMaintenanceView)

    def reindex(self):
        """ find all contentish objects (meaning all objects derived from one
            of the catalog mixin classes) and (re)indexes them """
        proc = queryUtility(ISolrIndexQueueProcessor, name='solr')
        def index(obj, path):
            if indexable(obj):
                proc.begin()
                proc.index(obj)
                proc.commit()
        self.context.ZopeFindAndApply(self.context, search_sub=True,
            apply_func=index)
        return 'solr reindexing finished.'

