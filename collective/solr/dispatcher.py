from zope.interface import implements
from zope.component import queryUtility
from Products.ZCatalog.ZCatalog import ZCatalog

from collective.solr.interfaces import ISearchDispatcher
from collective.solr.interfaces import ISearch
from collective.solr.utils import isActive, prepareData

from collective.solr.monkey import patchCatalogTool
patchCatalogTool()      # patch catalog tool to use the dispatcher...


class FallBackException(Exception):
    """ exception indicating the dispatcher should fall back to searching
        the portal catalog """


class SearchDispatcher(object):
    """ adapter for potentially dispatching a given query to an
        alternative search backend (instead of the portal catalog) """
    implements(ISearchDispatcher)

    def __init__(self, context):
        self.context = context

    def __call__(self, request, **keywords):
        """ decide on a search backend and perform the given query """
        if isActive():
            try:
                return solrSearchResults(request, **keywords)
            except FallBackException:
                pass
        return ZCatalog.searchResults(self.context, request, **keywords)


def solrSearchResults(request, **keywords):
    """ perform a query using solr after translating the passed in
        parameters with portal catalog semantics """
    search = queryUtility(ISearch)
    # FIXME: add translation/mangling of parameters
    if request is not None:
        keywords.update(request)
    if not keywords.has_key('SearchableText'):
        raise FallBackException
    prepareData(keywords)
    query = search.buildQuery(**keywords)
    return search(query)

