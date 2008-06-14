from zope.interface import implements
from zope.component import queryUtility, queryMultiAdapter
from zope.publisher.interfaces.http import IHTTPRequest
from Products.ZCatalog.ZCatalog import ZCatalog

from collective.solr.interfaces import ISearchDispatcher
from collective.solr.interfaces import ISearch
from collective.solr.interfaces import IFlare
from collective.solr.utils import isActive, prepareData
from collective.solr.mangler import mangleQuery

from collective.solr.monkey import patchCatalogTool
patchCatalogTool()      # patch catalog tool to use the dispatcher...

from collective.solr.attributes import registerAttributes
registerAttributes()    # register additional indexable attributes


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


def solrSearchResults(request=None, **keywords):
    """ perform a query using solr after translating the passed in
        parameters with portal catalog semantics """
    search = queryUtility(ISearch)
    if request is None:
        args = keywords
    elif IHTTPRequest.providedBy(request):
        args = request.form.copy()  # ignore headers and other stuff
        args.update(keywords)       # keywords take precedence
    else:
        assert isinstance(request, dict), request
        args = request.copy()
        args.update(keywords)       # keywords take precedence
    if not args.has_key('SearchableText'):
        raise FallBackException
    mangleQuery(args)
    prepareData(args)
    query = search.buildQuery(**args)
    results = search(query, fl='* score')
    def wrap(flare):
        """ wrap a flare object with a helper class """
        adapter = queryMultiAdapter((flare, request), IFlare)
        return adapter is not None and adapter or flare
    return map(wrap, results)

